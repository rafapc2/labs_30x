from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient

from gemela import auth, config, deps
from gemela.web import crear_app


@pytest.fixture(autouse=True)
def credenciales(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_CLIENT_ID", "id-gh")
    monkeypatch.setattr(config, "GITHUB_CLIENT_SECRET", "secreto-gh")
    monkeypatch.setattr(config, "GOOGLE_CLIENT_ID", "id-go")
    monkeypatch.setattr(config, "GOOGLE_CLIENT_SECRET", "secreto-go")


def _proveedor_simulado(identificador="42", nombre="Ana"):
    def manejar(request: httpx.Request):
        if request.url.path in ("/login/oauth/access_token", "/token"):
            return httpx.Response(200, json={"access_token": "tok"})
        return httpx.Response(200, json={"id": identificador, "sub": identificador, "name": nombre})

    return httpx.Client(transport=httpx.MockTransport(manejar))


@pytest.fixture
def cliente(conn):
    app = crear_app()

    def usar_conn():
        yield conn

    def usar_http():
        yield _proveedor_simulado()

    app.dependency_overrides[deps.get_conn] = usar_conn
    app.dependency_overrides[deps.get_cliente_http] = usar_http
    with TestClient(app, follow_redirects=False) as c:
        c.app_ = app
        yield c


def iniciar_sesion(cliente, proveedor="github"):
    r = cliente.get(f"/auth/{proveedor}/login")
    assert r.status_code == 302
    estado = parse_qs(urlparse(r.headers["location"]).query)["state"][0]
    return cliente.get(f"/auth/{proveedor}/callback", params={"code": "abc", "state": estado})


def test_login_redirige_al_proveedor_con_state(cliente):
    r = cliente.get("/auth/github/login")
    assert r.status_code == 302
    destino = urlparse(r.headers["location"])
    assert destino.netloc == "github.com"
    q = parse_qs(destino.query)
    assert q["client_id"] == ["id-gh"] and len(q["state"][0]) >= 32


def test_c17_api_sin_sesion_responde_401(cliente):
    assert cliente.get("/api/apps/00000000-0000-0000-0000-000000000000").status_code == 401


def test_inicio_de_sesion_crea_usuario_y_sesion(cliente, conn):
    r = iniciar_sesion(cliente)
    assert r.status_code == 302 and r.headers["location"] == "/"
    filas = conn.execute("SELECT proveedor, id_proveedor, nombre FROM usuarios").fetchall()
    assert filas == [{"proveedor": "github", "id_proveedor": "42", "nombre": "Ana"}]
    # con sesión ya no es 401: la app no existe, así que 404
    assert cliente.get("/api/apps/00000000-0000-0000-0000-000000000000").status_code == 404


def test_solo_se_guardan_proveedor_identificador_y_nombre(conn):
    cols = {r["column_name"] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'usuarios'")}
    assert cols == {"id", "proveedor", "id_proveedor", "nombre", "creado"}


def test_google_tambien_funciona(cliente, conn):
    assert iniciar_sesion(cliente, "google").status_code == 302
    assert conn.execute("SELECT proveedor FROM usuarios").fetchone()["proveedor"] == "google"


def test_c18_app_ajena_responde_404(cliente, conn):
    otro = conn.execute("INSERT INTO usuarios (proveedor, id_proveedor, nombre) VALUES ('github','99','Otro') RETURNING id").fetchone()["id"]
    ajena = conn.execute(
        "INSERT INTO apps (usuario_id, url, nombre, descripcion, token_verificacion) VALUES (%s,'https://x.example','X','d','t') RETURNING id",
        (otro,)).fetchone()["id"]
    iniciar_sesion(cliente)
    assert cliente.get(f"/api/apps/{ajena}").status_code == 404
    propia_id = conn.execute("SELECT id FROM usuarios WHERE id_proveedor='42'").fetchone()["id"]
    propia = conn.execute(
        "INSERT INTO apps (usuario_id, url, nombre, descripcion, token_verificacion) VALUES (%s,'https://y.example','Y','d','t') RETURNING id",
        (propia_id,)).fetchone()["id"]
    assert cliente.get(f"/api/apps/{propia}").status_code == 200


@pytest.mark.parametrize("ruta", ["/auth/facebook/login", "/auth/facebook/callback?code=a&state=b"])
def test_c19_proveedor_no_admitido_responde_404(cliente, ruta):
    assert cliente.get(ruta).status_code == 404


def test_proveedor_sin_credenciales_responde_404(cliente, monkeypatch):
    monkeypatch.setattr(config, "GITHUB_CLIENT_ID", "")
    assert cliente.get("/auth/github/login").status_code == 404


def test_c26_state_distinto_se_rechaza_y_no_crea_sesion(cliente, conn):
    cliente.get("/auth/github/login")
    r = cliente.get("/auth/github/callback", params={"code": "abc", "state": "otro-state"})
    assert r.status_code == 400
    assert conn.execute("SELECT count(*) AS n FROM usuarios").fetchone()["n"] == 0
    assert cliente.get("/api/apps/00000000-0000-0000-0000-000000000000").status_code == 401


def test_callback_sin_haber_pedido_login_se_rechaza(cliente):
    assert cliente.get("/auth/github/callback", params={"code": "abc", "state": "x"}).status_code == 400


def test_el_state_solo_sirve_una_vez(cliente):
    cliente.get("/auth/github/login")
    estado = parse_qs(urlparse(cliente.get("/auth/github/login").headers["location"]).query)["state"][0]
    assert cliente.get("/auth/github/callback", params={"code": "a", "state": estado}).status_code == 302
    assert cliente.get("/auth/github/callback", params={"code": "a", "state": estado}).status_code == 400


def test_logout_cierra_la_sesion(cliente):
    iniciar_sesion(cliente)
    assert cliente.post("/auth/logout").status_code == 204
    assert cliente.get("/api/apps/00000000-0000-0000-0000-000000000000").status_code == 401


def test_cookie_httponly_samesite_lax(cliente):
    cookie = cliente.get("/auth/github/login").headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "secure" not in cookie


def test_cookie_secure_con_https():
    app = crear_app("https://gemela.example")
    with TestClient(app, base_url="https://gemela.example", follow_redirects=False) as c:
        from gemela import config as cfg
        cfg.GITHUB_CLIENT_ID, cfg.GITHUB_CLIENT_SECRET = "a", "b"
        try:
            cookie = c.get("/auth/github/login").headers["set-cookie"].lower()
        finally:
            cfg.GITHUB_CLIENT_ID = cfg.GITHUB_CLIENT_SECRET = ""
    assert "secure" in cookie
