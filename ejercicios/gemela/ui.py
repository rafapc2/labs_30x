"""Páginas HTML de la interfaz. Se sirven en el puerto 8000, nunca por el túnel."""
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from gemela import api, auth, config
from gemela.deps import app_propia, get_conn, get_fabrica_modelo, get_lector

plantillas = Jinja2Templates(directory=str(Path(__file__).parent / "plantillas"))
router = APIRouter()


def _usuario(request: Request, conn):
    uid = request.session.get("usuario_id")
    if not uid:
        return None
    return conn.execute("SELECT id, nombre FROM usuarios WHERE id = %s", (uid,)).fetchone()


def _proveedores_configurados() -> list[str]:
    return [n for n, p in auth.PROVEEDORES.items() if p["id"]() and p["secreto"]()]


def _inicio(request, conn, usuario, error=None, url=None, estado=200):
    apps = []
    if usuario:
        apps = conn.execute("SELECT id, nombre, estado, verificada, url FROM apps WHERE usuario_id = %s ORDER BY creado DESC",
                            (usuario["id"],)).fetchall()
    return plantillas.TemplateResponse(request, "inicio.html", {
        "usuario": usuario, "proveedores": _proveedores_configurados(), "apps": apps, "error": error, "url": url,
    }, status_code=estado)


@router.get("/", response_class=HTMLResponse)
def inicio(request: Request, conn=Depends(get_conn)):
    return _inicio(request, conn, _usuario(request, conn))


@router.post("/analizar")
def analizar(request: Request, url: str = Form(""), conn=Depends(get_conn),
             leer=Depends(get_lector), fabrica_modelo=Depends(get_fabrica_modelo)):
    usuario = _usuario(request, conn)
    if not usuario:
        return RedirectResponse("/", status_code=303)
    try:
        # Mismo camino que la API: si la URL es inválida falla aquí, antes de leer el sitio o llamar al modelo.
        datos = api.crear_app(api.CrearApp(url=url), usuario, conn, leer, fabrica_modelo)
    except HTTPException as e:
        return _inicio(request, conn, usuario, error=e.detail, url=url, estado=e.status_code)
    return RedirectResponse(f"/apps/{datos['id']}", status_code=303)


def _pagina_de_app(request: Request, app_id: str, plantilla: str, conn, extra=None):
    usuario = _usuario(request, conn)
    if not usuario:
        return RedirectResponse("/", status_code=303)
    try:
        app = app_propia(app_id, usuario, conn)
    except HTTPException:
        raise HTTPException(status_code=404, detail="App no encontrada")
    contexto = {"usuario": usuario, "app": app, "herramientas": api._herramientas(conn, app["id"]),
                "url_mcp": f"{config.URL_MCP_PUBLICA.rstrip('/')}/apps/{app['id']}/mcp"}
    contexto.update((extra or (lambda a: {}))(app))
    return plantillas.TemplateResponse(request, plantilla, contexto)


@router.get("/apps/{app_id}", response_class=HTMLResponse)
def ver_app(request: Request, app_id: str, conn=Depends(get_conn)):
    return _pagina_de_app(request, app_id, "app.html", conn)


@router.get("/apps/{app_id}/panel", response_class=HTMLResponse)
def ver_panel(request: Request, app_id: str, conn=Depends(get_conn)):
    return _pagina_de_app(request, app_id, "panel.html", conn, lambda app: {"panel": api.panel(app, conn)})


@router.get("/apps/{app_id}/paquete", response_class=HTMLResponse)
def ver_paquete(request: Request, app_id: str, conn=Depends(get_conn)):
    # 403 si la app no está verificada, igual que en la API (BR-MCP-03).
    return _pagina_de_app(request, app_id, "paquete.html", conn, lambda app: {"paquete": api._paquete_de(app, conn)})


@router.post("/auth/logout-web")
def salir(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
