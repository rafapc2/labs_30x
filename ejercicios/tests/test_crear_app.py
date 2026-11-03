import time

import httpx
import pytest
from fastapi.testclient import TestClient

from conftest import HOST_EJEMPLO, dependencia_conn, resolvedor_publico, transporte_de
from gemela import config, deps, extractor, lector, llm
from gemela.web import crear_app
from test_auth import _proveedor_simulado, credenciales, iniciar_sesion  # noqa: F401

URL = f"https://{HOST_EJEMPLO}/"
RESPUESTA = {
    "nombre": "Panadería La Espiga", "descripcion_corta": "Pan artesanal", "descripcion": "Pan, pasteles y café desde 1987.",
    "descripcion_larga": "Una panadería del centro.", "categoria": "Comida",
    "herramientas": {"buscar": "Busca.", "contacto": "Contacto.", "listar_paginas": "Lista."},
}


def montar(conn, paginas, resolvedor=resolvedor_publico, modelo=None, relanzar=True):
    app = crear_app()
    app.dependency_overrides[deps.get_conn] = dependencia_conn(conn)
    app.dependency_overrides[deps.get_cliente_http] = lambda: _proveedor_simulado()
    app.dependency_overrides[deps.get_lector] = lambda: (
        lambda url: lector.leer_sitio(url, resolvedor=resolvedor, transporte=transporte_de(paginas)))
    app.dependency_overrides[deps.get_fabrica_modelo] = lambda: (lambda: modelo or llm.ModeloSimulado(RESPUESTA))
    c = TestClient(app, follow_redirects=False, raise_server_exceptions=relanzar)
    iniciar_sesion(c)
    return c


@pytest.fixture
def cliente(conn, paginas_ejemplo):
    with montar(conn, paginas_ejemplo) as c:
        yield c


def _contar(conn):
    return {t: conn.execute(f"SELECT count(*) AS n FROM {t}").fetchone()["n"] for t in ("apps", "contenido", "herramientas")}


def test_c1_crea_la_app_con_nombre_descripcion_y_herramientas(cliente, conn):
    r = cliente.post("/api/apps", json={"url": URL})
    assert r.status_code == 200
    j = r.json()
    assert j["nombre"] == "Panadería La Espiga" and j["descripcion"]
    assert [h["nombre"] for h in j["herramientas"]] == ["buscar", "contacto", "listar_paginas"]
    assert _contar(conn) == {"apps": 1, "contenido": 3, "herramientas": 3}
    assert cliente.get(f"/api/apps/{j['id']}").json()["estado"] == "borrador"


def test_c22_incluye_token_de_verificacion_unico(cliente, conn):
    a = cliente.post("/api/apps", json={"url": URL}).json()
    b = cliente.post("/api/apps", json={"url": URL}).json()
    assert len(a["token_verificacion"]) >= 24 and a["token_verificacion"] != b["token_verificacion"]
    assert conn.execute("SELECT token_verificacion FROM apps WHERE id = %s", (a["id"],)).fetchone()["token_verificacion"] == a["token_verificacion"]


def test_c20_la_sexta_creacion_en_una_hora_responde_429(cliente, conn):
    for _ in range(5):
        assert cliente.post("/api/apps", json={"url": URL}).status_code == 200
    r = cliente.post("/api/apps", json={"url": URL})
    assert r.status_code == 429 and _contar(conn)["apps"] == 5


def test_c20_las_apps_de_hace_mas_de_una_hora_no_cuentan(cliente, conn):
    for _ in range(5):
        cliente.post("/api/apps", json={"url": URL})
    conn.execute("UPDATE apps SET creado = now() - interval '2 hours'")
    assert cliente.post("/api/apps", json={"url": URL}).status_code == 200


def test_c20_el_limite_es_por_cuenta(cliente, conn):
    for _ in range(5):
        cliente.post("/api/apps", json={"url": URL})
    conn.execute("INSERT INTO usuarios (proveedor, id_proveedor, nombre) VALUES ('github','7','Otra')")
    conn.execute("UPDATE apps SET usuario_id = (SELECT id FROM usuarios WHERE id_proveedor = '7')")
    assert cliente.post("/api/apps", json={"url": URL}).status_code == 200


@pytest.mark.parametrize("url", ["ejemplo.com", "ftp://x.example", "", "http://"])
def test_c2_url_invalida_responde_422_y_no_crea_nada(cliente, conn, url):
    assert cliente.post("/api/apps", json={"url": url}).status_code == 422
    assert _contar(conn)["apps"] == 0


def test_falta_el_campo_url_responde_422(cliente):
    assert cliente.post("/api/apps", json={}).status_code == 422


def test_c3_sitio_que_no_responde_responde_502_y_no_crea_nada(conn, paginas_ejemplo):
    def cae(url):
        raise lector.ErrorSitio("El sitio no responde")

    c = montar(conn, paginas_ejemplo)
    c.app.dependency_overrides[deps.get_lector] = lambda: cae
    assert c.post("/api/apps", json={"url": URL}).status_code == 502
    assert _contar(conn) == {"apps": 0, "contenido": 0, "herramientas": 0}


def test_c4_direccion_privada_responde_422_sin_peticiones(conn, paginas_ejemplo):
    transporte = transporte_de(paginas_ejemplo)
    c = montar(conn, paginas_ejemplo)
    c.app.dependency_overrides[deps.get_lector] = lambda: (
        lambda url: lector.leer_sitio(url, resolvedor=lambda h, p: ["10.0.0.5"], transporte=transporte))
    assert c.post("/api/apps", json={"url": URL}).status_code == 422
    assert transporte.peticiones == [] and _contar(conn)["apps"] == 0


def test_c5_robots_prohibe_responde_422_con_el_motivo(conn):
    c = montar(conn, {"/robots.txt": "User-agent: *\nDisallow: /", "/": "<html></html>"})
    r = c.post("/api/apps", json={"url": URL})
    assert r.status_code == 422 and "robots.txt" in r.json()["detail"] and _contar(conn)["apps"] == 0


def test_fallo_del_modelo_responde_502_y_no_deja_filas(conn, paginas_ejemplo):
    c = montar(conn, paginas_ejemplo, modelo=llm.ModeloSimulado(llm.ErrorModelo("cayó")))
    assert c.post("/api/apps", json={"url": URL}).status_code == 502
    assert _contar(conn) == {"apps": 0, "contenido": 0, "herramientas": 0}


def test_sin_clave_de_openai_responde_502(conn, paginas_ejemplo, monkeypatch):
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    c = montar(conn, paginas_ejemplo)
    c.app.dependency_overrides[deps.get_fabrica_modelo] = lambda: llm.ModeloOpenAI
    r = c.post("/api/apps", json={"url": URL})
    assert r.status_code == 502 and "OPENAI_API_KEY" in r.json()["detail"]


def test_plazo_vencido_responde_502_y_no_deja_filas(conn, paginas_ejemplo, monkeypatch):
    monkeypatch.setattr(config, "PLAZO_ANALISIS", 0.2)

    def lento(url):
        time.sleep(1.0)
        return []

    c = montar(conn, paginas_ejemplo)
    c.app.dependency_overrides[deps.get_lector] = lambda: lento
    inicio = time.monotonic()
    r = c.post("/api/apps", json={"url": URL})
    assert r.status_code == 502 and time.monotonic() - inicio < 0.9
    assert _contar(conn)["apps"] == 0


def test_un_fallo_al_guardar_revierte_todo(conn, paginas_ejemplo, monkeypatch):
    def falla(*a, **k):
        raise RuntimeError("disco lleno")

    monkeypatch.setattr(extractor, "guardar_contenido", falla)
    c = montar(conn, paginas_ejemplo, relanzar=False)
    assert c.post("/api/apps", json={"url": URL}).status_code == 500
    assert _contar(conn) == {"apps": 0, "contenido": 0, "herramientas": 0}


def test_sin_sesion_responde_401(conn, paginas_ejemplo):
    c = montar(conn, paginas_ejemplo)
    c.post("/auth/logout")
    assert c.post("/api/apps", json={"url": URL}).status_code == 401
