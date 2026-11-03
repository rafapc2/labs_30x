import json
from types import SimpleNamespace

import pytest

from gemela import config, deps, herramientas, llm
from test_auth import credenciales  # noqa: F401
from test_ciclo_app import montar, nueva_app
from test_servidor_mcp import url_servidor  # noqa: F401


@pytest.fixture
def api(conn, paginas_ejemplo, url_servidor):
    c = montar(conn, paginas_ejemplo)
    yield c


def usar_modelo(api, modelo):
    api.app.dependency_overrides[deps.get_fabrica_modelo] = lambda: (lambda: modelo)


def test_c13_un_mensaje_sobre_un_dato_del_sitio_indica_la_herramienta_invocada(api):
    datos = nueva_app(api)
    usar_modelo(api, llm.ModeloSimulado(eleccion=lambda m: ("buscar", {"consulta": m})))
    r = api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "¿Qué horario tienen los viernes?"})
    assert r.status_code == 200
    j = r.json()
    assert j["herramienta"] == "buscar" and "horarios.html" in j["respuesta"]


def test_sin_herramienta_la_respuesta_no_indica_ninguna(api):
    datos = nueva_app(api)
    usar_modelo(api, llm.ModeloSimulado())
    assert api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "hola"}).json()["herramienta"] is None


def test_funciona_sin_verificacion(api, conn):
    datos = nueva_app(api)
    assert conn.execute("SELECT verificada FROM apps WHERE id=%s", (datos["id"],)).fetchone()["verificada"] is False
    usar_modelo(api, llm.ModeloSimulado())
    assert api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "hola"}).status_code == 200


def test_c24_el_mensaje_31_en_una_hora_responde_429(api, conn):
    datos = nueva_app(api)
    usar_modelo(api, llm.ModeloSimulado())
    for _ in range(30):
        assert api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "hola"}).status_code == 200
    assert api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "hola"}).status_code == 429


def test_c24_los_mensajes_de_hace_mas_de_una_hora_no_cuentan(api, conn):
    datos = nueva_app(api)
    usar_modelo(api, llm.ModeloSimulado())
    for _ in range(30):
        api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "hola"})
    conn.execute("UPDATE uso_simulador SET fecha = now() - interval '2 hours'")
    conn.commit()
    assert api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "hola"}).status_code == 200


@pytest.mark.parametrize("mensaje", ["", "   ", "x" * 2001])
def test_mensaje_invalido_responde_422_y_no_gasta_cuota(api, conn, mensaje):
    datos = nueva_app(api)
    usar_modelo(api, llm.ModeloSimulado())
    assert api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": mensaje}).status_code == 422
    assert conn.execute("SELECT count(*) AS n FROM uso_simulador").fetchone()["n"] == 0


def test_no_se_guarda_el_texto_del_mensaje(api, conn):
    datos = nueva_app(api)
    usar_modelo(api, llm.ModeloSimulado())
    api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "TEXTO-PRIVADO-123"})
    cols = {r["column_name"] for r in conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name='uso_simulador'")}
    assert cols == {"id", "usuario_id", "fecha"}


def test_fallo_del_modelo_responde_502_pero_la_cuota_se_gasta(api, conn):
    datos = nueva_app(api)
    usar_modelo(api, llm.ModeloSimulado(eleccion=llm.ErrorModelo("cayó")))
    assert api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "hola"}).status_code == 502
    assert conn.execute("SELECT count(*) AS n FROM uso_simulador").fetchone()["n"] == 1


def test_el_simulador_usa_las_mismas_funciones_que_el_servidor_mcp(api, monkeypatch):
    datos = nueva_app(api)
    llamadas = []
    original = herramientas.ejecutar
    monkeypatch.setattr(herramientas, "ejecutar", lambda *a, **k: (llamadas.append(a[2]), original(*a, **k))[1])
    usar_modelo(api, llm.ModeloSimulado(eleccion=("contacto", {})))
    api.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "contacto"})
    assert llamadas == ["contacto"]


def test_app_ajena_responde_404(conn, paginas_ejemplo, url_servidor):
    a, b = montar(conn, paginas_ejemplo), montar(conn, paginas_ejemplo, id_usuario="99")
    datos = nueva_app(a)
    assert b.post(f"/api/apps/{datos['id']}/simulador", json={"mensaje": "hola"}).status_code == 404


# ---- ModeloOpenAI.conversar con un cliente falso: herramienta -> resultado -> respuesta final ----

class _Falso:
    def __init__(self):
        self.llamadas = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._crear))

    def _crear(self, **kw):
        self.llamadas.append(kw)
        if len(self.llamadas) == 1:
            t = SimpleNamespace(id="t1", function=SimpleNamespace(name="buscar", arguments=json.dumps({"consulta": "horario"})))
            msg = SimpleNamespace(content=None, tool_calls=[t])
        else:
            msg = SimpleNamespace(content="Abren de lunes a viernes.", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_conversar_ejecuta_la_herramienta_y_devuelve_la_respuesta_final():
    falso, ejecutadas = _Falso(), []
    defs = [{"nombre": "buscar", "descripcion": "d", "esquema": herramientas.DEFINICIONES["buscar"]}]
    texto, usada = llm.ModeloOpenAI(falso).conversar("s", "¿horario?", defs, lambda n, a: ejecutadas.append((n, a)) or ["x"])
    assert (texto, usada) == ("Abren de lunes a viernes.", "buscar") and ejecutadas == [("buscar", {"consulta": "horario"})]
    assert "tools" in falso.llamadas[0] and "tools" not in falso.llamadas[1]
    assert falso.llamadas[1]["messages"][-1]["role"] == "tool"
