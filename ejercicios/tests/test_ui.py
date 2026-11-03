import pytest
from fastapi.testclient import TestClient

from conftest import dependencia_conn
from gemela import config, deps, llm
from gemela.web import crear_app
from test_auth import _proveedor_simulado, credenciales, iniciar_sesion  # noqa: F401
from test_ciclo_app import montar, nueva_app
from test_crear_app import RESPUESTA, URL
from test_servidor_mcp import CABECERAS, leer, rpc, url_servidor  # noqa: F401


@pytest.fixture
def api(conn, paginas_ejemplo, url_servidor):
    return montar(conn, paginas_ejemplo)


def anonimo(conn):
    app = crear_app()
    app.dependency_overrides[deps.get_conn] = dependencia_conn(conn)
    return TestClient(app, follow_redirects=False)


def test_sin_sesion_el_inicio_ofrece_iniciar_sesion(conn):
    r = anonimo(conn).get("/")
    assert r.status_code == 200 and "Continuar con Github" in r.text and "Continuar con Google" in r.text
    assert 'name="url"' not in r.text


def test_sin_proveedores_configurados_lo_dice(conn, monkeypatch):
    for n in ("GITHUB_CLIENT_ID", "GOOGLE_CLIENT_ID"):
        monkeypatch.setattr(config, n, "")
    assert "No hay ningún proveedor" in anonimo(conn).get("/").text


def test_con_sesion_el_formulario_exige_una_url(api):
    html = api.get("/").text
    assert 'type="url"' in html and "required" in html and 'action="/analizar"' in html


def test_url_invalida_muestra_el_error_junto_al_campo_y_no_lee_el_sitio(api):
    llamadas = []
    api.app.dependency_overrides[deps.get_lector] = lambda: (lambda url: llamadas.append(url))
    r = api.post("/analizar", data={"url": "ejemplo.com"})
    assert r.status_code == 422
    html = r.text
    assert html.index('name="url"') < html.index('id="error-url"') < html.index("Generar app")
    assert "http://" in html[html.index('id="error-url"'):html.index('id="error-url"') + 200]
    assert 'value="ejemplo.com"' in html  # conserva lo escrito
    assert llamadas == []  # el analizador nunca se invocó


def test_url_valida_crea_la_app_y_redirige_a_su_pagina(api):
    r = api.post("/analizar", data={"url": URL})
    assert r.status_code == 303 and r.headers["location"].startswith("/apps/")
    pagina = api.get(r.headers["location"]).text
    assert "Panadería La Espiga" in pagina and "buscar" in pagina and "aproximación" in pagina
    assert 'name="mcp-gemela"' in pagina  # instrucciones de verificación con el token


def test_el_inicio_lista_las_apps_del_usuario(api):
    nueva_app(api)
    assert "Panadería La Espiga" in api.get("/").text


def test_sin_sesion_las_paginas_de_apps_redirigen_al_inicio(conn):
    c = anonimo(conn)
    for ruta in ("/apps/00000000-0000-0000-0000-000000000000", "/apps/00000000-0000-0000-0000-000000000000/panel"):
        r = c.get(ruta)
        assert r.status_code == 303 and r.headers["location"] == "/"
    assert c.post("/analizar", data={"url": URL}).status_code == 303


def test_la_app_de_otra_cuenta_responde_404(conn, paginas_ejemplo, url_servidor):
    a, b = montar(conn, paginas_ejemplo), montar(conn, paginas_ejemplo, id_usuario="99")
    datos = nueva_app(a)
    assert b.get(f"/apps/{datos['id']}").status_code == 404
    assert b.get(f"/apps/{datos['id']}/panel").status_code == 404


def test_el_panel_muestra_las_llamadas_sin_texto(api):
    datos = nueva_app(api)
    assert "Sin llamadas todavía" in api.get(f"/apps/{datos['id']}/panel").text


def test_el_contenido_del_modelo_se_escapa_en_la_pagina(api):
    peligroso = {**RESPUESTA, "nombre": "<script>alert(1)</script>", "descripcion": "<img src=x onerror=alert(2)>"}
    api.app.dependency_overrides[deps.get_fabrica_modelo] = lambda: (lambda: llm.ModeloSimulado(peligroso))
    r = api.post("/analizar", data={"url": URL})
    html = api.get(r.headers["location"]).text
    assert "<script>alert(1)</script>" not in html and "<img src=x" not in html
    assert "&lt;script&gt;" in html


def test_cerrar_sesion_desde_la_web(api):
    assert api.post("/auth/logout-web").status_code == 303
    assert api.get("/api/apps/00000000-0000-0000-0000-000000000000").status_code == 401
