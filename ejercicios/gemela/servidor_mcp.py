"""Servidor MCP multi-app (puerto 8001). Es lo único que se expone por el túnel (ADR 0002).

Un solo `Server` de MCP atiende todas las apps. La app se identifica por la ruta
`/apps/{id}/mcp`, que el manejador lee de la petición HTTP. El transporte es HTTP en
streaming, en modo sin estado, así que no hay sesiones que guardar.
"""
import contextlib
import json
import uuid

import anyio
import mcp.types as tipos
from fastapi import FastAPI
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse

from gemela import db, herramientas

servidor = Server("gemela")


def _app_id_de_la_peticion() -> str:
    peticion = servidor.request_context.request
    return peticion.scope["path_params"]["app_id"]


def _herramientas_de(app_id: str) -> list[dict]:
    with db.conectar() as conn:
        return conn.execute("SELECT nombre, descripcion FROM herramientas WHERE app_id = %s ORDER BY id", (app_id,)).fetchall()


def _ejecutar_y_registrar(app_id: str, nombre: str, argumentos: dict):
    """Ejecuta la herramienta y registra la llamada (herramienta, fecha, ok o error). Nunca guarda los argumentos."""
    conocida = nombre in herramientas.DEFINICIONES
    try:
        with db.conectar() as conn:
            resultado = herramientas.ejecutar(conn, app_id, nombre, argumentos)
        ok = True
    except Exception as e:
        resultado, ok = f"Error: {e}", False
    with db.conectar() as conn:
        conn.execute(
            "INSERT INTO llamadas (app_id, herramienta, resultado) VALUES (%s, %s, %s)",
            (app_id, nombre if conocida else "(desconocida)", "ok" if ok else "error"),
        )
    return ok, resultado


@servidor.list_tools()
async def listar_herramientas() -> list[tipos.Tool]:
    filas = await anyio.to_thread.run_sync(_herramientas_de, _app_id_de_la_peticion())
    return [
        tipos.Tool(name=f["nombre"], description=f["descripcion"],
                   inputSchema=herramientas.DEFINICIONES.get(f["nombre"], {"type": "object", "properties": {}}),
                   annotations=tipos.ToolAnnotations(readOnlyHint=True))
        for f in filas
    ]


# validate_input=False: la validación la hace `herramientas.ejecutar`, así un argumento inválido también cuenta como error.
@servidor.call_tool(validate_input=False)
async def llamar_herramienta(nombre: str, argumentos: dict | None) -> tipos.CallToolResult:
    ok, resultado = await anyio.to_thread.run_sync(
        _ejecutar_y_registrar, _app_id_de_la_peticion(), nombre, argumentos or {})
    texto = json.dumps(resultado, ensure_ascii=False) if ok else str(resultado)
    return tipos.CallToolResult(content=[tipos.TextContent(type="text", text=texto)], isError=not ok)


def _crear_gestor() -> StreamableHTTPSessionManager:
    # La ruta MCP es pública y no usa cookies ni credenciales (BR-MCP-08), así que no hay nada que un
    # ataque de reasignación de DNS pueda aprovechar. Se deja la protección desactivada de forma explícita.
    return StreamableHTTPSessionManager(
        app=servidor, stateless=True,
        security_settings=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )


@contextlib.asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # Un gestor solo puede arrancar una vez (lo dice el SDK): se crea uno nuevo en cada arranque.
    app.state.gestor = _crear_gestor()
    async with app.state.gestor.run():
        yield


app = FastAPI(title="Gemela: servidor MCP", lifespan=ciclo_de_vida)


@app.get("/salud")
def salud() -> dict:
    return {"estado": "ok", "servicio": "mcp"}


def _app_desplegada(app_id: str) -> bool:
    try:
        uuid.UUID(app_id)
    except ValueError:
        return False
    with db.conectar() as conn:
        fila = conn.execute("SELECT 1 FROM apps WHERE id = %s AND estado = 'desplegada'", (app_id,)).fetchone()
    return fila is not None


class _RutaMcp:
    """Ruta ASGI directa: el gestor de MCP escribe la respuesta él mismo, sin pasar por FastAPI."""

    async def __call__(self, scope, receive, send):
        app_id = scope["path_params"]["app_id"]
        # 404 para apps inexistentes, en borrador o retiradas (BR-MCP-09), sin distinguir cuál de los casos es.
        if not await anyio.to_thread.run_sync(_app_desplegada, app_id):
            await JSONResponse({"detail": "App no encontrada"}, status_code=404)(scope, receive, send)
            return
        await scope["app"].state.gestor.handle_request(scope, receive, send)


app.add_route("/apps/{app_id}/mcp", _RutaMcp(), methods=["GET", "POST", "DELETE"])
