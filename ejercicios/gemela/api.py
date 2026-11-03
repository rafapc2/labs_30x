"""Endpoints `/api/*`. Todos exigen sesión (401 sin ella)."""
import secrets
from concurrent.futures import ThreadPoolExecutor, TimeoutError as PlazoVencido
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from gemela import config, extractor, generador, herramientas, lector
from gemela.deps import (app_propia, get_conn, get_fabrica_cliente_verificacion, get_fabrica_modelo, get_lector,
                         usuario_actual)
from gemela.llm import ErrorModelo

router = APIRouter(prefix="/api", dependencies=[Depends(usuario_actual)])


class CrearApp(BaseModel):
    url: str


def _herramientas(conn, app_id) -> list[dict]:
    filas = conn.execute("SELECT nombre, descripcion FROM herramientas WHERE app_id = %s ORDER BY id", (app_id,)).fetchall()
    return [{"nombre": f["nombre"], "descripcion": f["descripcion"]} for f in filas]


@router.get("/apps/{app_id}")
def ver_app(app=Depends(app_propia), conn=Depends(get_conn)) -> dict:
    return {"id": str(app["id"]), "url": app["url"], "nombre": app["nombre"], "descripcion": app["descripcion"],
            "estado": app["estado"], "verificada": app["verificada"], "herramientas": _herramientas(conn, app["id"])}


def _analizar(url: str, leer, fabrica_modelo):
    """Descarga, extrae y genera. No toca la base de datos: así un fallo o un plazo vencido no deja nada a medias."""
    paginas = leer(url)
    analisis = extractor.analizar(paginas)
    metadata = generador.generar_metadata(analisis, fabrica_modelo(), nombre_sitio=urlparse(url).hostname or "")
    return analisis, metadata


@router.post("/apps")
def crear_app(cuerpo: CrearApp, usuario=Depends(usuario_actual), conn=Depends(get_conn),
              leer=Depends(get_lector), fabrica_modelo=Depends(get_fabrica_modelo)) -> dict:
    try:
        url = lector.validar_url(cuerpo.url)
    except lector.ErrorURL as e:
        raise HTTPException(status_code=422, detail=str(e))
    recientes = conn.execute(
        "SELECT count(*) AS n FROM apps WHERE usuario_id = %s AND creado > now() - interval '1 hour'", (usuario["id"],)
    ).fetchone()["n"]
    if recientes >= config.MAX_APPS_POR_HORA:
        raise HTTPException(status_code=429, detail=f"Máximo {config.MAX_APPS_POR_HORA} apps por hora")

    ejecutor = ThreadPoolExecutor(max_workers=1)
    futuro = ejecutor.submit(_analizar, url, leer, fabrica_modelo)
    try:
        analisis, metadata = futuro.result(timeout=config.PLAZO_ANALISIS)
    except PlazoVencido:
        raise HTTPException(status_code=502, detail="El análisis tardó demasiado")
    except lector.ErrorURL as e:  # incluye robots.txt: se informa el motivo
        raise HTTPException(status_code=422, detail=str(e))
    except lector.ErrorSitio as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ErrorModelo as e:
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        ejecutor.shutdown(wait=False)

    token = secrets.token_urlsafe(24)
    app_id = conn.execute(
        "INSERT INTO apps (usuario_id, url, nombre, descripcion, descripcion_corta, descripcion_larga, categoria, token_verificacion) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (usuario["id"], url, metadata.nombre, metadata.descripcion, metadata.descripcion_corta,
         metadata.descripcion_larga, metadata.categoria, token),
    ).fetchone()["id"]
    extractor.guardar_contenido(conn, app_id, analisis)
    for nombre, descripcion in metadata.herramientas.items():
        conn.execute("INSERT INTO herramientas (app_id, nombre, descripcion) VALUES (%s, %s, %s)", (app_id, nombre, descripcion))
    return {"id": str(app_id), "url": url, "nombre": metadata.nombre, "descripcion": metadata.descripcion,
            "herramientas": _herramientas(conn, app_id), "token_verificacion": token}


# ---------- Verificación de propiedad (S3, S7) ----------

def _origen(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _token_en_el_sitio(cliente, url: str, token: str) -> bool:
    from bs4 import BeautifulSoup

    base = _origen(url)
    r = cliente.get(f"{base}/")
    if r.status_code < 400 and "html" in r.headers.get("content-type", "").lower():
        for meta in BeautifulSoup(r.text, "html.parser").find_all("meta", attrs={"name": "mcp-gemela"}):
            if secrets.compare_digest(str(meta.get("content", "")).strip(), token):
                return True
    r = cliente.get(f"{base}/.well-known/mcp-gemela.txt")
    return r.status_code < 400 and secrets.compare_digest(r.text.strip(), token)


@router.post("/apps/{app_id}/verificacion")
def verificar(app=Depends(app_propia), conn=Depends(get_conn),
              fabrica_cliente=Depends(get_fabrica_cliente_verificacion)) -> dict:
    if app["verificada"]:
        return {"verificada": True}
    try:
        with fabrica_cliente() as cliente:
            encontrado = _token_en_el_sitio(cliente, app["url"], app["token_verificacion"])
    except lector.ErrorURL as e:  # misma regla de direcciones no públicas que el lector (C4)
        raise HTTPException(status_code=422, detail=str(e))
    except (lector.ErrorSitio, httpx.HTTPError) as e:
        raise HTTPException(status_code=502, detail=f"No se pudo consultar el sitio: {e}")
    if not encontrado:
        raise HTTPException(status_code=409, detail="No se encontró el token de verificación en el sitio")
    conn.execute("UPDATE apps SET verificada = true WHERE id = %s", (app["id"],))
    return {"verificada": True}


# ---------- Despliegue y retiro (BR-MCP-03, BR-MCP-09) ----------

@router.post("/apps/{app_id}/despliegue")
def desplegar(app=Depends(app_propia), conn=Depends(get_conn)) -> dict:
    if not app["verificada"]:
        raise HTTPException(status_code=403, detail="Verifica la propiedad del sitio antes de desplegar")
    conn.execute("UPDATE apps SET estado = 'desplegada' WHERE id = %s", (app["id"],))
    return {"estado": "desplegada", "url_mcp": f"{config.URL_MCP_PUBLICA.rstrip('/')}/apps/{app['id']}/mcp"}


@router.post("/apps/{app_id}/retiro")
def retirar(app=Depends(app_propia), conn=Depends(get_conn)) -> dict:
    if app["estado"] != "desplegada":
        raise HTTPException(status_code=409, detail="Solo se puede retirar una app desplegada")
    conn.execute("UPDATE apps SET estado = 'retirada' WHERE id = %s", (app["id"],))
    return {"estado": "retirada"}


# ---------- Panel de uso (BR-MCP-05, BR-MCP-07) ----------

@router.get("/apps/{app_id}/panel")
def panel(app=Depends(app_propia), conn=Depends(get_conn)) -> dict:
    """Solo contadores: llamadas por día, por herramienta, errores y la última llamada. Nunca el texto."""
    por_dia = conn.execute(
        "SELECT (fecha AT TIME ZONE 'UTC')::date AS dia, count(*) AS n FROM llamadas WHERE app_id = %s GROUP BY dia ORDER BY dia",
        (app["id"],)).fetchall()
    por_herramienta = conn.execute(
        "SELECT herramienta, count(*) AS n FROM llamadas WHERE app_id = %s GROUP BY herramienta ORDER BY herramienta",
        (app["id"],)).fetchall()
    total = conn.execute(
        "SELECT count(*) AS n, count(*) FILTER (WHERE resultado = 'error') AS errores, max(fecha) AS ultima "
        "FROM llamadas WHERE app_id = %s", (app["id"],)).fetchone()
    return {
        "total": total["n"], "errores": total["errores"],
        "ultima_llamada": total["ultima"].isoformat() if total["ultima"] else None,
        "por_dia": {str(f["dia"]): f["n"] for f in por_dia},
        "por_herramienta": {f["herramienta"]: f["n"] for f in por_herramienta},
    }


# ---------- Simulador de ChatGPT (S4, S13) ----------

class MensajeSimulador(BaseModel):
    mensaje: str


def _definiciones(conn, app_id) -> list[dict]:
    return [{"nombre": h["nombre"], "descripcion": h["descripcion"],
             "esquema": herramientas.DEFINICIONES.get(h["nombre"], {"type": "object", "properties": {}})}
            for h in _herramientas(conn, app_id)]


@router.post("/apps/{app_id}/simulador")
def simulador(cuerpo: MensajeSimulador, app=Depends(app_propia), usuario=Depends(usuario_actual),
              conn=Depends(get_conn), fabrica_modelo=Depends(get_fabrica_modelo)) -> dict:
    """Funciona sin verificación (BR-MCP-03). No guarda el texto del mensaje ni de la respuesta."""
    mensaje = cuerpo.mensaje.strip()
    if not mensaje or len(mensaje) > 2000:
        raise HTTPException(status_code=422, detail="El mensaje debe tener entre 1 y 2000 caracteres")
    usados = conn.execute(
        "SELECT count(*) AS n FROM uso_simulador WHERE usuario_id = %s AND fecha > now() - interval '1 hour'",
        (usuario["id"],)).fetchone()["n"]
    if usados >= config.MAX_MENSAJES_SIMULADOR_POR_HORA:
        raise HTTPException(status_code=429, detail=f"Máximo {config.MAX_MENSAJES_SIMULADOR_POR_HORA} mensajes por hora")
    conn.execute("INSERT INTO uso_simulador (usuario_id) VALUES (%s)", (usuario["id"],))
    conn.commit()  # el uso cuenta aunque el modelo falle: ya se gastó la cuota
    sistema = (f"Eres ChatGPT con la app «{app['nombre']}» instalada. Responde usando sus herramientas y solo con la "
               "información que devuelvan; si no hay información, dilo. Responde en el idioma del usuario.")
    try:
        respuesta, usada = fabrica_modelo().conversar(
            sistema, mensaje, _definiciones(conn, app["id"]),
            lambda nombre, args: herramientas.ejecutar(conn, app["id"], nombre, args))
    except ErrorModelo as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"respuesta": respuesta, "herramienta": usada}


# ---------- Paquete de publicación (spec 6.10, ADR 0003) ----------

def _paquete_de(app, conn) -> dict:
    from gemela import paquete as _paquete

    if not app["verificada"]:
        raise HTTPException(status_code=403, detail="Verifica la propiedad del sitio para obtener el paquete")
    paginas = herramientas.listar_paginas(conn, app["id"])
    url_mcp = f"{config.URL_MCP_PUBLICA.rstrip('/')}/apps/{app['id']}/mcp"
    return _paquete.construir(app, _herramientas(conn, app["id"]), paginas, url_mcp)


@router.get("/apps/{app_id}/paquete")
def paquete(app=Depends(app_propia), conn=Depends(get_conn)) -> dict:
    return _paquete_de(app, conn)


@router.get("/apps/{app_id}/paquete.zip")
def paquete_zip(app=Depends(app_propia), conn=Depends(get_conn)):
    from fastapi.responses import Response

    from gemela import paquete as _paquete

    contenido = _paquete.zip_bytes(_paquete_de(app, conn))
    return Response(contenido, media_type="application/zip",
                    headers={"content-disposition": f'attachment; filename="{_paquete.slug(app["nombre"])}.zip"'})
