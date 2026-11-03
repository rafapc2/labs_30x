"""Los tres criterios de aceptación de la spec (sección 4), de punta a punta y sin pasos manuales.

Usan el sitio de ejemplo, el modelo simulado y el servidor MCP real montado como aplicación ASGI.
"""
import re

import pytest
from fastapi.testclient import TestClient

from gemela import servidor_mcp
from test_auth import credenciales  # noqa: F401
from test_ciclo_app import con_token, montar
from test_crear_app import URL
from test_servidor_mcp import CABECERAS, leer, rpc, url_servidor  # noqa: F401

TRES = ["buscar", "contacto", "listar_paginas"]


@pytest.fixture
def api(conn, paginas_ejemplo, url_servidor):
    return montar(conn, paginas_ejemplo)


@pytest.fixture
def mcp(url_servidor):
    with TestClient(servidor_mcp.app) as m:
        yield m


def _herramientas_en_la_pagina(html: str) -> list[str]:
    seccion = html.split("<h2>Herramientas</h2>")[1].split("<h2>Probar")[0]
    return re.findall(r"<code>(\w+)</code>", seccion)


def test_criterio_1_url_valida_muestra_una_app_con_nombre_descripcion_y_las_tres_herramientas(api):
    r = api.post("/analizar", data={"url": URL})
    assert r.status_code == 303
    pagina = api.get(r.headers["location"]).text  # la vista con el simulador
    assert "Panadería La Espiga" in pagina and "Pan, pasteles y café desde 1987." in pagina
    assert _herramientas_en_la_pagina(pagina) == TRES
    assert 'id="form-sim"' in pagina  # el simulador está en la misma vista
    # las descripciones se generaron a partir del sitio (el modelo simulado las devuelve) y no están vacías
    descripciones = api.get(r.headers["location"].replace("/apps/", "/api/apps/")).json()["herramientas"]
    assert all(h["descripcion"] for h in descripciones)


def test_criterio_2_tras_verificar_y_confirmar_la_url_mcp_responde_las_mismas_herramientas(api, mcp):
    datos = api.post("/api/apps", json={"url": URL}).json()
    en_el_simulador = _herramientas_en_la_pagina(api.get(f"/apps/{datos['id']}").text)
    assert api.post(f"/api/apps/{datos['id']}/despliegue").status_code == 403  # sin verificar no se despliega
    con_token(api, datos)
    assert api.post(f"/api/apps/{datos['id']}/verificacion").status_code == 200
    ruta = re.sub(r"^https?://[^/]+", "", api.post(f"/api/apps/{datos['id']}/despliegue").json()["url_mcp"])
    r = mcp.post(ruta, json=rpc("tools/list", {}), headers=CABECERAS)
    assert r.status_code == 200
    assert [t["name"] for t in leer(r)["result"]["tools"]] == en_el_simulador == TRES


def test_criterio_3_tras_llamar_una_herramienta_el_panel_cuenta_la_llamada(api, mcp):
    datos = api.post("/api/apps", json={"url": URL}).json()
    con_token(api, datos)
    api.post(f"/api/apps/{datos['id']}/verificacion")
    ruta = re.sub(r"^https?://[^/]+", "", api.post(f"/api/apps/{datos['id']}/despliegue").json()["url_mcp"])
    antes = api.get(f"/api/apps/{datos['id']}/panel").json()["por_herramienta"].get("contacto", 0)
    r = mcp.post(ruta, headers=CABECERAS, json=rpc("tools/call", {"name": "contacto", "arguments": {}}))
    assert leer(r)["result"]["isError"] is False
    despues = api.get(f"/api/apps/{datos['id']}/panel").json()["por_herramienta"]["contacto"]
    assert despues == antes + 1
    assert ">1<" in api.get(f"/apps/{datos['id']}/panel").text  # y se ve en la página del panel
