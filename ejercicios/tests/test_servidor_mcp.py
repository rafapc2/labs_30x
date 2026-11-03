import json
import uuid

import pytest
from fastapi.testclient import TestClient

from conftest import dependencia_conn  # noqa: F401
from gemela import db, servidor_mcp

CABECERAS = {"content-type": "application/json", "accept": "application/json, text/event-stream"}


def rpc(metodo, params=None, id=1):
    return {"jsonrpc": "2.0", "id": id, "method": metodo, **({"params": params} if params is not None else {})}


def leer(respuesta):
    """La respuesta puede ser JSON o un flujo SSE con un evento `data:`."""
    texto = respuesta.text
    if respuesta.headers["content-type"].startswith("text/event-stream"):
        linea = [l for l in texto.splitlines() if l.startswith("data:")][0]
        return json.loads(linea[5:].strip())
    return json.loads(texto)


@pytest.fixture
def url_servidor(url_bd, monkeypatch):
    monkeypatch.setattr(db.config, "DATABASE_URL", url_bd)
    return url_bd


def crear_app_desplegada(conn, estado="desplegada", herramientas_=("buscar", "contacto", "listar_paginas")):
    uid = conn.execute("INSERT INTO usuarios (proveedor, id_proveedor, nombre) VALUES ('github', %s, 'Ana') RETURNING id", (str(uuid.uuid4()),)).fetchone()["id"]
    app = conn.execute(
        "INSERT INTO apps (usuario_id, url, nombre, descripcion, token_verificacion, estado, verificada) VALUES (%s,'https://x.example','X','d','t',%s,true) RETURNING id",
        (uid, estado)).fetchone()["id"]
    for n in herramientas_:
        conn.execute("INSERT INTO herramientas (app_id, nombre, descripcion) VALUES (%s,%s,%s)", (app, n, f"Descripción de {n}"))
    conn.execute("INSERT INTO contenido (app_id, url, titulo, texto) VALUES (%s,'https://x.example/h','Horarios','Abrimos de lunes a viernes por la mañana')", (app,))
    conn.commit()
    return app


@pytest.fixture
def cliente(conn, url_servidor):
    with TestClient(servidor_mcp.app) as c:
        yield c


def test_salud(cliente):
    assert cliente.get("/salud").json()["servicio"] == "mcp"


def test_c16_responde_la_lista_de_herramientas_por_http_en_streaming(cliente, conn):
    app = crear_app_desplegada(conn)
    r = cliente.post(f"/apps/{app}/mcp", json=rpc("tools/list", {}), headers=CABECERAS)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")  # transporte HTTP en streaming (SSE)
    nombres = [t["name"] for t in leer(r)["result"]["tools"]]
    assert nombres == ["buscar", "contacto", "listar_paginas"]
    buscar = [t for t in leer(r)["result"]["tools"] if t["name"] == "buscar"][0]
    assert buscar["inputSchema"]["required"] == ["consulta"] and buscar["annotations"]["readOnlyHint"] is True


def test_cada_app_expone_sus_propias_herramientas(cliente, conn):
    a = crear_app_desplegada(conn, herramientas_=("buscar",))
    b = crear_app_desplegada(conn, herramientas_=("contacto", "listar_paginas"))
    na = [t["name"] for t in leer(cliente.post(f"/apps/{a}/mcp", json=rpc("tools/list", {}), headers=CABECERAS))["result"]["tools"]]
    nb = [t["name"] for t in leer(cliente.post(f"/apps/{b}/mcp", json=rpc("tools/list", {}), headers=CABECERAS))["result"]["tools"]]
    assert na == ["buscar"] and nb == ["contacto", "listar_paginas"]


def test_inicializacion_funciona(cliente, conn):
    app = crear_app_desplegada(conn)
    r = cliente.post(f"/apps/{app}/mcp", headers=CABECERAS, json=rpc("initialize", {
        "protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "prueba", "version": "1"}}))
    assert r.status_code == 200 and "serverInfo" in leer(r)["result"]


def llamar(cliente, app, nombre, argumentos):
    r = cliente.post(f"/apps/{app}/mcp", headers=CABECERAS, json=rpc("tools/call", {"name": nombre, "arguments": argumentos}))
    return r, leer(r)["result"]


def test_llamar_a_una_herramienta_devuelve_resultado_y_registra_la_llamada(cliente, conn):
    app = crear_app_desplegada(conn)
    r, res = llamar(cliente, app, "buscar", {"consulta": "horario viernes"})
    assert res["isError"] is False and "Horarios" in res["content"][0]["text"]
    assert conn.execute("SELECT herramienta, resultado FROM llamadas WHERE app_id = %s", (app,)).fetchall() == [
        {"herramienta": "buscar", "resultado": "ok"}]


def test_c12_llamada_con_error_se_registra_como_error_y_no_guarda_la_consulta(cliente, conn):
    app = crear_app_desplegada(conn)
    secreto = "MI-CONSULTA-PRIVADA"
    _, res = llamar(cliente, app, "buscar", {"consulta": 123, "otro": secreto})
    assert res["isError"] is True
    _, res2 = llamar(cliente, app, "borrar_todo", {"x": secreto})
    assert res2["isError"] is True
    filas = conn.execute("SELECT herramienta, resultado FROM llamadas WHERE app_id = %s ORDER BY id", (app,)).fetchall()
    assert filas == [{"herramienta": "buscar", "resultado": "error"}, {"herramienta": "(desconocida)", "resultado": "error"}]
    volcado = json.dumps(conn.execute("SELECT * FROM llamadas").fetchall(), default=str)
    assert secreto not in volcado


@pytest.mark.parametrize("estado", ["borrador", "retirada"])
def test_c21_app_que_no_esta_desplegada_responde_404(cliente, conn, estado):
    app = crear_app_desplegada(conn, estado=estado)
    assert cliente.post(f"/apps/{app}/mcp", json=rpc("tools/list", {}), headers=CABECERAS).status_code == 404


def test_c21_retirar_una_app_desplegada_la_deja_en_404(cliente, conn):
    app = crear_app_desplegada(conn)
    assert cliente.post(f"/apps/{app}/mcp", json=rpc("tools/list", {}), headers=CABECERAS).status_code == 200
    conn.execute("UPDATE apps SET estado = 'retirada' WHERE id = %s", (app,))
    conn.commit()
    assert cliente.post(f"/apps/{app}/mcp", json=rpc("tools/list", {}), headers=CABECERAS).status_code == 404


@pytest.mark.parametrize("ruta", [f"/apps/{uuid.uuid4()}/mcp", "/apps/no-es-un-uuid/mcp", "/apps/1/mcp"])
def test_apps_inexistentes_responden_404(cliente, ruta):
    assert cliente.post(ruta, json=rpc("tools/list", {}), headers=CABECERAS).status_code == 404


def test_este_servicio_no_expone_la_interfaz_ni_la_api(cliente):
    for ruta in ["/", "/api/apps", "/auth/github/login", "/api/apps/x/panel"]:
        assert cliente.get(ruta).status_code == 404
