"""Verificación, despliegue, retiro y panel, con las dos aplicaciones (API y servidor MCP) sobre la misma base."""
import json

import pytest
from fastapi.testclient import TestClient

from conftest import dependencia_conn, resolvedor_publico, transporte_de
from gemela import deps, lector, llm, servidor_mcp
from gemela.web import crear_app
from test_auth import _proveedor_simulado, credenciales, iniciar_sesion  # noqa: F401
from test_crear_app import RESPUESTA, URL
from test_servidor_mcp import CABECERAS, leer, rpc, url_servidor  # noqa: F401

LISTA = rpc("tools/list", {})


def montar(conn, paginas, id_usuario="42", resolvedor=resolvedor_publico):
    app = crear_app()
    sitio = dict(paginas)  # el sitio que ve la verificación; las pruebas le añaden el token
    app.dependency_overrides[deps.get_conn] = dependencia_conn(conn)
    app.dependency_overrides[deps.get_cliente_http] = lambda: _proveedor_simulado(identificador=id_usuario)
    app.dependency_overrides[deps.get_lector] = lambda: (
        lambda url: lector.leer_sitio(url, resolvedor=resolvedor, transporte=transporte_de(paginas)))
    app.dependency_overrides[deps.get_fabrica_modelo] = lambda: (lambda: llm.ModeloSimulado(RESPUESTA))
    app.dependency_overrides[deps.get_fabrica_cliente_verificacion] = lambda: (
        lambda: lector.crear_cliente(resolvedor, transporte_de(sitio)))
    c = TestClient(app, follow_redirects=False)
    iniciar_sesion(c)
    c.sitio = sitio
    return c


@pytest.fixture
def api(conn, paginas_ejemplo, url_servidor):
    with montar(conn, paginas_ejemplo) as c:
        yield c


@pytest.fixture
def mcp(url_servidor):
    with TestClient(servidor_mcp.app) as m:
        yield m


def nueva_app(api):
    r = api.post("/api/apps", json={"url": URL})
    assert r.status_code == 200
    return r.json()


def con_token(api, datos, como="meta"):
    if como == "meta":
        api.sitio["/"] = f'<html><head><meta name="mcp-gemela" content="{datos["token_verificacion"]}"></head><body>Hola</body></html>'
    else:
        api.sitio["/.well-known/mcp-gemela.txt"] = datos["token_verificacion"] + "\n"


def verificada(api):
    datos = nueva_app(api)
    con_token(api, datos)
    assert api.post(f"/api/apps/{datos['id']}/verificacion").status_code == 200
    return datos


def herramientas_mcp(mcp, app_id):
    r = mcp.post(f"/apps/{app_id}/mcp", json=LISTA, headers=CABECERAS)
    return r.status_code, [t["name"] for t in leer(r)["result"]["tools"]] if r.status_code == 200 else None


# ---- Verificación (C8, C9, C22, C4) ----

@pytest.mark.parametrize("como", ["meta", "archivo"])
def test_c8_con_el_token_presente_la_app_queda_verificada(api, conn, como):
    datos = nueva_app(api)
    con_token(api, datos, como)
    r = api.post(f"/api/apps/{datos['id']}/verificacion")
    assert r.status_code == 200 and r.json() == {"verificada": True}
    assert conn.execute("SELECT verificada FROM apps WHERE id = %s", (datos["id"],)).fetchone()["verificada"] is True


def test_c9_sin_el_token_responde_409_y_no_verifica(api, conn):
    datos = nueva_app(api)
    assert api.post(f"/api/apps/{datos['id']}/verificacion").status_code == 409
    assert conn.execute("SELECT verificada FROM apps WHERE id = %s", (datos["id"],)).fetchone()["verificada"] is False


def test_c22_el_token_de_otra_app_falla_con_409(api):
    a, b = nueva_app(api), nueva_app(api)
    con_token(api, a)
    assert api.post(f"/api/apps/{b['id']}/verificacion").status_code == 409
    assert api.post(f"/api/apps/{a['id']}/verificacion").status_code == 200


def test_un_token_incorrecto_responde_409(api):
    datos = nueva_app(api)
    api.sitio["/"] = '<meta name="mcp-gemela" content="otro-token">'
    assert api.post(f"/api/apps/{datos['id']}/verificacion").status_code == 409


def test_c4_la_verificacion_tambien_bloquea_direcciones_privadas(api):
    datos = nueva_app(api)
    transporte = transporte_de({})
    api.app.dependency_overrides[deps.get_fabrica_cliente_verificacion] = lambda: (
        lambda: lector.crear_cliente(lambda h, p: ["10.0.0.5"], transporte))
    assert api.post(f"/api/apps/{datos['id']}/verificacion").status_code == 422
    assert transporte.peticiones == []


def test_verificar_una_app_ajena_responde_404(conn, paginas_ejemplo, url_servidor):
    with montar(conn, paginas_ejemplo) as a, montar(conn, paginas_ejemplo, id_usuario="99") as b:
        datos = nueva_app(a)
        assert b.post(f"/api/apps/{datos['id']}/verificacion").status_code == 404


# ---- Despliegue y retiro (C7, C10, C21) ----

def test_c7_despliegue_sin_verificacion_responde_403(api, conn):
    datos = nueva_app(api)
    assert api.post(f"/api/apps/{datos['id']}/despliegue").status_code == 403
    assert conn.execute("SELECT estado FROM apps WHERE id = %s", (datos["id"],)).fetchone()["estado"] == "borrador"


def test_c10_el_despliegue_devuelve_la_url_mcp_con_las_mismas_herramientas_que_el_simulador(api, mcp):
    datos = verificada(api)
    assert herramientas_mcp(mcp, datos["id"])[0] == 404  # antes de desplegar no responde
    r = api.post(f"/api/apps/{datos['id']}/despliegue")
    assert r.status_code == 200 and r.json()["url_mcp"].endswith(f"/apps/{datos['id']}/mcp")
    en_api = [h["nombre"] for h in api.get(f"/api/apps/{datos['id']}").json()["herramientas"]]
    assert herramientas_mcp(mcp, datos["id"]) == (200, en_api)


def test_c21_tras_el_retiro_la_lista_de_herramientas_responde_404(api, mcp):
    datos = verificada(api)
    api.post(f"/api/apps/{datos['id']}/despliegue")
    assert herramientas_mcp(mcp, datos["id"])[0] == 200
    assert api.post(f"/api/apps/{datos['id']}/retiro").json() == {"estado": "retirada"}
    assert herramientas_mcp(mcp, datos["id"])[0] == 404


def test_se_puede_volver_a_desplegar_una_app_retirada(api, mcp):
    datos = verificada(api)
    api.post(f"/api/apps/{datos['id']}/despliegue")
    api.post(f"/api/apps/{datos['id']}/retiro")
    assert api.post(f"/api/apps/{datos['id']}/despliegue").status_code == 200
    assert herramientas_mcp(mcp, datos["id"])[0] == 200


@pytest.mark.parametrize("preparar", ["borrador", "retirada"])
def test_solo_se_retira_una_app_desplegada(api, preparar):
    datos = verificada(api)
    if preparar == "retirada":
        api.post(f"/api/apps/{datos['id']}/despliegue")
        api.post(f"/api/apps/{datos['id']}/retiro")
    assert api.post(f"/api/apps/{datos['id']}/retiro").status_code == 409


# ---- Panel (C11, C12, C18) ----

def llamar(mcp, app_id, nombre, args):
    r = mcp.post(f"/apps/{app_id}/mcp", headers=CABECERAS, json=rpc("tools/call", {"name": nombre, "arguments": args}))
    return leer(r)["result"]


def test_panel_vacio(api):
    datos = nueva_app(api)
    assert api.get(f"/api/apps/{datos['id']}/panel").json() == {
        "total": 0, "errores": 0, "ultima_llamada": None, "por_dia": {}, "por_herramienta": {}}


def test_c11_tras_una_llamada_el_contador_de_esa_herramienta_aumenta(api, mcp):
    datos = verificada(api)
    api.post(f"/api/apps/{datos['id']}/despliegue")
    llamar(mcp, datos["id"], "buscar", {"consulta": "horarios"})
    llamar(mcp, datos["id"], "contacto", {})
    llamar(mcp, datos["id"], "buscar", {"consulta": "pan"})
    p = api.get(f"/api/apps/{datos['id']}/panel").json()
    assert p["total"] == 3 and p["errores"] == 0 and p["por_herramienta"] == {"buscar": 2, "contacto": 1}
    assert p["ultima_llamada"] and sum(p["por_dia"].values()) == 3


def test_c12_una_llamada_con_error_suma_un_error_y_no_aparece_el_texto(api, mcp):
    datos = verificada(api)
    api.post(f"/api/apps/{datos['id']}/despliegue")
    llamar(mcp, datos["id"], "buscar", {"consulta": 5, "nota": "TEXTO-PRIVADO"})
    p = api.get(f"/api/apps/{datos['id']}/panel").json()
    assert p["errores"] == 1 and p["por_herramienta"] == {"buscar": 1}
    assert "TEXTO-PRIVADO" not in json.dumps(p)


def test_c18_otra_cuenta_recibe_404_en_el_panel(conn, paginas_ejemplo, url_servidor):
    with montar(conn, paginas_ejemplo) as a, montar(conn, paginas_ejemplo, id_usuario="99") as b:
        datos = nueva_app(a)
        assert b.get(f"/api/apps/{datos['id']}/panel").status_code == 404
        assert a.get(f"/api/apps/{datos['id']}/panel").status_code == 200
