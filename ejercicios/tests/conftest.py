"""Fixtures compartidas. Las pruebas usan el PostgreSQL real del compose, con una base aparte."""
import os

import psycopg
import pytest

from gemela import db

URL_ADMIN = os.environ.get("TEST_DB_ADMIN_URL", "postgresql://gemela:gemela@localhost:5433/postgres")
URL_TEST = os.environ.get("TEST_DATABASE_URL", "postgresql://gemela:gemela@localhost:5433/gemela_test")
TABLAS = "uso_simulador, llamadas, herramientas, contenido, apps, usuarios"


@pytest.fixture(scope="session")
def url_bd():
    """Crea la base `gemela_test` si no existe y aplica las migraciones."""
    try:
        with psycopg.connect(URL_ADMIN, autocommit=True) as admin:
            existe = admin.execute("SELECT 1 FROM pg_database WHERE datname = 'gemela_test'").fetchone()
            if not existe:
                admin.execute("CREATE DATABASE gemela_test")
    except psycopg.OperationalError as e:
        pytest.skip(f"PostgreSQL no disponible (levanta `docker compose up -d postgres`): {e}")
    with db.conectar(URL_TEST) as conn:
        db.aplicar(conn)
    return URL_TEST


@pytest.fixture
def conn(url_bd):
    """Conexión con las tablas vacías al empezar cada prueba."""
    c = db.conectar(url_bd)
    c.execute(f"TRUNCATE {TABLAS} RESTART IDENTITY CASCADE")
    c.commit()
    yield c
    c.rollback()
    c.close()


# --- Sitio de ejemplo y red simulada (el guardia de direcciones bloquea localhost, y debe seguir bloqueándolo) ---
from pathlib import Path

import httpx

CARPETA_SITIO = Path(__file__).parent / "fixtures" / "sitio_ejemplo"
HOST_EJEMPLO = "www.laespiga.example"
IP_PUBLICA = "93.184.216.34"


def resolvedor_publico(host, puerto):
    return [IP_PUBLICA]


def transporte_de(paginas: dict[str, str], tipo="text/html; charset=utf-8"):
    """MockTransport que sirve `paginas` (ruta -> contenido) y registra las peticiones."""
    peticiones = []

    def manejar(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        if request.url.path in paginas:
            t = "text/plain" if request.url.path == "/robots.txt" else tipo
            return httpx.Response(200, text=paginas[request.url.path], headers={"content-type": t})
        return httpx.Response(404, text="no existe")

    transporte = httpx.MockTransport(manejar)
    transporte.peticiones = peticiones
    return transporte


@pytest.fixture
def paginas_ejemplo():
    out = {f"/{p.name}": p.read_text(encoding="utf-8") for p in CARPETA_SITIO.iterdir()}
    out["/"] = out["/index.html"]
    return out


@pytest.fixture
def transporte_ejemplo(paginas_ejemplo):
    return transporte_de(paginas_ejemplo)


def dependencia_conn(conn):
    """Sustituto de `deps.get_conn` que usa la conexión de la prueba y se comporta igual: confirma o revierte."""
    def _dep():
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return _dep
