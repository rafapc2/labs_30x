import io
import json
import zipfile

import pytest

from gemela import config, paquete
from test_auth import credenciales  # noqa: F401
from test_ciclo_app import montar, verificada, nueva_app
from test_servidor_mcp import url_servidor  # noqa: F401


@pytest.fixture
def api(conn, paginas_ejemplo, url_servidor):
    return montar(conn, paginas_ejemplo)


def test_c7_sin_verificar_el_paquete_responde_403(api):
    datos = nueva_app(api)
    assert api.get(f"/api/apps/{datos['id']}/paquete").status_code == 403
    assert api.get(f"/api/apps/{datos['id']}/paquete.zip").status_code == 403
    assert api.get(f"/apps/{datos['id']}/paquete").status_code == 403


def test_c14_el_paquete_incluye_campos_ocho_casos_textos_y_guia(api):
    datos = verificada(api)
    p = api.get(f"/api/apps/{datos['id']}/paquete").json()
    campos = p["campos"]
    assert campos["displayName"] == "Panadería La Espiga" and campos["websiteURL"].startswith("https://")
    assert {"displayName", "shortDescription", "longDescription", "developerName", "category",
            "websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"} <= set(campos)
    assert len(p["casos_de_prueba"]["positive"]) == 5 and len(p["casos_de_prueba"]["negative"]) == 3
    assert "Política de privacidad" in p["politica_privacidad"] and "Términos de servicio" in p["terminos"]
    assert len(p["guia"]) >= 6


def test_c14_cada_herramienta_de_los_casos_existe_en_la_app(api):
    datos = verificada(api)
    p = api.get(f"/api/apps/{datos['id']}/paquete").json()
    existentes = {h["nombre"] for h in api.get(f"/api/apps/{datos['id']}").json()["herramientas"]}
    for caso in p["casos_de_prueba"]["positive"]:
        assert caso["tools_triggered"] and set(caso["tools_triggered"]) <= existentes and caso["expected_behavior"]
    for caso in p["casos_de_prueba"]["negative"]:
        assert "tools_triggered" not in caso and caso["expected_behavior"]


def test_c25_la_descripcion_corta_larga_se_acorta_a_30(api, conn):
    datos = verificada(api)
    conn.execute("UPDATE apps SET descripcion_corta = %s, nombre = %s WHERE id = %s",
                 ("Una panadería artesanal del centro con más de treinta años", "N" * 80, datos["id"]))
    conn.commit()
    campos = api.get(f"/api/apps/{datos['id']}/paquete").json()["campos"]
    assert 0 < len(campos["shortDescription"]) <= 30 and 0 < len(campos["displayName"]) <= 30


def test_la_descripcion_larga_no_pasa_de_4000(api, conn):
    datos = verificada(api)
    conn.execute("UPDATE apps SET descripcion_larga = %s WHERE id = %s", ("palabra " * 1000, datos["id"]))
    conn.commit()
    assert len(api.get(f"/api/apps/{datos['id']}/paquete").json()["campos"]["longDescription"]) <= 4000


def test_lo_que_solo_puede_aportar_el_dueno_queda_marcado_y_listado(api):
    datos = verificada(api)
    p = api.get(f"/api/apps/{datos['id']}/paquete").json()
    for k in ("developerName", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
        assert p["campos"][k] == paquete.PENDIENTE and k in p["pendiente_del_dueno"]
    assert "iconos" in p["pendiente_del_dueno"] and "demo_recording_url" in p["pendiente_del_dueno"]


def test_url_mcp_no_https_genera_advertencia(api, monkeypatch):
    datos = verificada(api)
    monkeypatch.setattr(config, "URL_MCP_PUBLICA", "http://localhost:8001")
    assert api.get(f"/api/apps/{datos['id']}/paquete").json()["advertencias"]
    monkeypatch.setattr(config, "URL_MCP_PUBLICA", "https://mcp.ejemplo.com")
    p = api.get(f"/api/apps/{datos['id']}/paquete").json()
    assert p["advertencias"] == [] and p["mcp_json"]["mcpServers"]["panaderia-la-espiga"]["url"].startswith("https://mcp.ejemplo.com/apps/")


def test_el_zip_sigue_la_disposicion_agent_plugins_del_adr_0003(api):
    datos = verificada(api)
    r = api.get(f"/api/apps/{datos['id']}/paquete.zip")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    assert 'filename="panaderia-la-espiga.zip"' in r.headers["content-disposition"]
    z = zipfile.ZipFile(io.BytesIO(r.content))
    nombres = set(z.namelist())
    assert {"plugin.json", "mcp.json", "skills/empezar/SKILL.md"} <= nombres
    plugin, mcp = json.loads(z.read("plugin.json")), json.loads(z.read("mcp.json"))
    assert plugin["name"] == "panaderia-la-espiga" and plugin["version"] == "1.0.0"
    assert "interface" in plugin["extensions"]["com.openai"]
    servidor = list(mcp["mcpServers"].values())[0]
    assert servidor["type"] == "streamable-http" and servidor["url"].endswith("/mcp") and "headers" not in servidor
    assert "test_credentials" not in z.read("plugin.json").decode() and "reviewer_instructions" not in z.read("plugin.json").decode()
    assert z.read("skills/empezar/SKILL.md").decode().startswith("---\nname: empezar\ndescription:")


def test_el_zip_no_referencia_archivos_que_no_incluye(api):
    datos = verificada(api)
    z = zipfile.ZipFile(io.BytesIO(api.get(f"/api/apps/{datos['id']}/paquete.zip").content))
    texto = z.read("plugin.json").decode()
    for clave in ("composerIcon", "logo", "screenshots", "./assets"):
        assert clave not in texto


@pytest.mark.parametrize("nombre,esperado", [("Panadería La Espiga", "panaderia-la-espiga"), ("  ¡Hola!!  Mundo  ", "hola-mundo"),
                                              ("日本語", "app-gemela"), ("a" * 100, "a" * 64)])
def test_slug_cumple_las_reglas_del_nombre(nombre, esperado):
    assert paquete.slug(nombre) == esperado


def test_la_pagina_del_paquete_muestra_guia_y_descarga(api):
    datos = verificada(api)
    html = api.get(f"/apps/{datos['id']}/paquete").text
    assert "Descargar ZIP" in html and "El envío lo haces tú" in html and "PENDIENTE" in html
    assert html.count("Herramientas:") == 5


def test_app_ajena_responde_404(conn, paginas_ejemplo, url_servidor):
    a, b = montar(conn, paginas_ejemplo), montar(conn, paginas_ejemplo, id_usuario="99")
    datos = verificada(a)
    assert b.get(f"/api/apps/{datos['id']}/paquete").status_code == 404
