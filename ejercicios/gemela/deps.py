"""Dependencias de FastAPI: base de datos, sesión, propiedad de las apps y cliente HTTP."""
import uuid

import httpx
from fastapi import Depends, HTTPException, Request

from gemela import db


def get_conn():
    conn = db.conectar()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_cliente_http():
    """Cliente para hablar con los proveedores OAuth. Las pruebas lo sustituyen."""
    with httpx.Client(timeout=10.0) as cliente:
        yield cliente


def usuario_actual(request: Request, conn=Depends(get_conn)) -> dict:
    """401 si no hay sesión válida (C17)."""
    uid = request.session.get("usuario_id")
    usuario = conn.execute("SELECT id, nombre, proveedor FROM usuarios WHERE id = %s", (uid,)).fetchone() if uid else None
    if not usuario:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar")
    return usuario


def app_propia(app_id: str, usuario=Depends(usuario_actual), conn=Depends(get_conn)) -> dict:
    """La app debe existir y ser de la cuenta; si es ajena responde 404 sin revelar que existe (BR-MCP-07, C18)."""
    try:
        uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="App no encontrada")
    app = conn.execute("SELECT * FROM apps WHERE id = %s AND usuario_id = %s", (app_id, usuario["id"])).fetchone()
    if not app:
        raise HTTPException(status_code=404, detail="App no encontrada")
    return app


def get_lector():
    """Función que descarga un sitio. Las pruebas la sustituyen por una con red simulada."""
    from gemela import lector

    return lector.leer_sitio


def get_fabrica_modelo():
    """Devuelve una fábrica, para que la falta de clave sea un 502 y no un error al arrancar."""
    from gemela import llm

    return llm.ModeloOpenAI


def get_fabrica_cliente_verificacion():
    """Fábrica del cliente HTTP seguro para comprobar la propiedad. Las pruebas la sustituyen."""
    from gemela import lector

    return lector.crear_cliente
