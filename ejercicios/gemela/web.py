"""Interfaz web y API (puerto 8000). Nunca se expone por el túnel."""
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from gemela import api, auth, config, ui


def crear_app(url_base: str | None = None) -> FastAPI:
    url_base = url_base or config.URL_BASE
    app = FastAPI(title="Gemela: interfaz y API")
    # Cookie HttpOnly (por defecto en Starlette), SameSite=Lax, y Secure con HTTPS (S14).
    app.add_middleware(
        SessionMiddleware, secret_key=config.SECRETO_SESION, session_cookie="gemela_sesion",
        same_site="lax", https_only=url_base.startswith("https://"), max_age=60 * 60 * 24 * 7,
    )
    app.include_router(auth.router)
    app.include_router(api.router)
    app.include_router(ui.router)

    @app.get("/salud")
    def salud() -> dict:
        return {"estado": "ok", "servicio": "api"}

    return app


app = crear_app()
