"""Inicio de sesión con Google o GitHub (OAuth 2.0) y sesión por cookie."""
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response

from gemela import config
from gemela.deps import get_cliente_http, get_conn

router = APIRouter(prefix="/auth")

PROVEEDORES = {
    "github": {
        "autorizar": "https://github.com/login/oauth/authorize",
        "token": "https://github.com/login/oauth/access_token",
        "usuario": "https://api.github.com/user",
        "scope": "read:user",
        "id": lambda: config.GITHUB_CLIENT_ID,
        "secreto": lambda: config.GITHUB_CLIENT_SECRET,
    },
    "google": {
        "autorizar": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "usuario": "https://openidconnect.googleapis.com/v1/userinfo",
        "scope": "openid profile",
        "id": lambda: config.GOOGLE_CLIENT_ID,
        "secreto": lambda: config.GOOGLE_CLIENT_SECRET,
    },
}


def _proveedor(nombre: str) -> dict:
    """404 si el proveedor no existe o no está configurado (C19)."""
    p = PROVEEDORES.get(nombre)
    if not p or not p["id"]() or not p["secreto"]():
        raise HTTPException(status_code=404, detail="Proveedor no disponible")
    return p


def _retorno(nombre: str) -> str:
    return f"{config.URL_BASE.rstrip('/')}/auth/{nombre}/callback"


@router.get("/{proveedor}/login")
def login(proveedor: str, request: Request):
    p = _proveedor(proveedor)
    estado = secrets.token_urlsafe(32)
    request.session["oauth_state"] = estado
    params = {"client_id": p["id"](), "redirect_uri": _retorno(proveedor), "scope": p["scope"], "state": estado}
    if proveedor == "google":
        params["response_type"] = "code"
    return RedirectResponse(f"{p['autorizar']}?{urlencode(params)}", status_code=302)


@router.get("/{proveedor}/callback")
def callback(proveedor: str, request: Request, code: str = "", state: str = "",
             conn=Depends(get_conn), cliente: httpx.Client = Depends(get_cliente_http)):
    p = _proveedor(proveedor)
    esperado = request.session.pop("oauth_state", None)
    # C26: un state distinto del emitido se rechaza y no crea sesión.
    if not esperado or not state or not secrets.compare_digest(esperado, state) or not code:
        raise HTTPException(status_code=400, detail="Inicio de sesión rechazado")
    try:
        datos = {"client_id": p["id"](), "client_secret": p["secreto"](), "code": code, "redirect_uri": _retorno(proveedor)}
        if proveedor == "google":
            datos["grant_type"] = "authorization_code"
        r = cliente.post(p["token"], data=datos, headers={"Accept": "application/json"})
        token = r.json().get("access_token")
        if not token:
            raise HTTPException(status_code=400, detail="Inicio de sesión rechazado")
        info = cliente.get(p["usuario"], headers={"Authorization": f"Bearer {token}"}).json()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="No se pudo contactar al proveedor")
    id_proveedor = str(info.get("id") if proveedor == "github" else info.get("sub") or "")
    if not id_proveedor or id_proveedor == "None":
        raise HTTPException(status_code=400, detail="Inicio de sesión rechazado")
    nombre = (info.get("name") or info.get("login") or "Sin nombre")[:100]
    # Solo se guardan proveedor, identificador y nombre.
    fila = conn.execute(
        "INSERT INTO usuarios (proveedor, id_proveedor, nombre) VALUES (%s, %s, %s) "
        "ON CONFLICT (proveedor, id_proveedor) DO UPDATE SET nombre = EXCLUDED.nombre RETURNING id",
        (proveedor, id_proveedor, nombre),
    ).fetchone()
    request.session.clear()
    request.session["usuario_id"] = fila["id"]
    return RedirectResponse("/", status_code=302)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return Response(status_code=204)
