from fastapi.testclient import TestClient

from gemela.servidor_mcp import app as app_mcp
from gemela.web import app as app_web


def test_salud_api():
    r = TestClient(app_web).get("/salud")
    assert r.status_code == 200 and r.json()["servicio"] == "api"


def test_salud_mcp():
    r = TestClient(app_mcp).get("/salud")
    assert r.status_code == 200 and r.json()["servicio"] == "mcp"
