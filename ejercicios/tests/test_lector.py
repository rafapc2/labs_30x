import socket

import httpx
import pytest

from conftest import HOST_EJEMPLO, resolvedor_publico, transporte_de
from gemela import lector
from gemela.lector import ErrorRobots, ErrorSitio, ErrorURL, leer_sitio, validar_url

URL = f"https://{HOST_EJEMPLO}/"


def test_lee_el_sitio_de_ejemplo(transporte_ejemplo):
    paginas = leer_sitio(URL, resolvedor=resolvedor_publico, transporte=transporte_ejemplo)
    urls = {p.url for p in paginas}
    assert urls == {URL, f"https://{HOST_EJEMPLO}/horarios.html", f"https://{HOST_EJEMPLO}/contacto.html"}
    # no sigue enlaces a otros dominios ni mailto
    assert all(HOST_EJEMPLO in str(r.url) for r in transporte_ejemplo.peticiones)


@pytest.mark.parametrize("url", ["ejemplo.com", "ftp://ejemplo.com", "javascript:alert(1)", "https://", "", "   "])
def test_c2_url_sin_http_o_https_se_rechaza(url):
    with pytest.raises(ErrorURL):
        validar_url(url)


def test_c3_dominio_que_no_responde():
    def falla(request):
        raise httpx.ConnectError("sin conexión")

    with pytest.raises(ErrorSitio):
        leer_sitio(URL, resolvedor=resolvedor_publico, transporte=httpx.MockTransport(falla))


def test_c3_dominio_que_no_resuelve():
    def no_resuelve(host, puerto):
        raise ErrorSitio("no resuelve")

    with pytest.raises(ErrorSitio):
        leer_sitio(URL, resolvedor=no_resuelve, transporte=transporte_de({}))


def test_c4_direccion_privada_se_rechaza_sin_hacer_la_peticion(transporte_ejemplo):
    privado = lambda host, puerto: ["10.0.0.5"]
    with pytest.raises(ErrorURL):
        leer_sitio(URL, resolvedor=privado, transporte=transporte_ejemplo)
    assert transporte_ejemplo.peticiones == []


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/", "http://localhost.example/", "http://169.254.169.254/latest/meta-data/",
    "http://[::1]/", "http://10.1.2.3/", "http://192.168.0.1/", "http://100.64.0.1/", "http://[::ffff:127.0.0.1]/",
])
def test_ip_literales_no_publicas_se_rechazan_o_resuelven_a_no_publicas(url):
    transporte = transporte_de({"/": "<html></html>"})
    loopback = lambda host, puerto: ["127.0.0.1"]
    with pytest.raises(ErrorURL):
        leer_sitio(url, resolvedor=loopback, transporte=transporte)
    assert transporte.peticiones == []


def test_redireccion_hacia_direccion_privada_se_bloquea():
    ips = {HOST_EJEMPLO: "93.184.216.34", "interno.example": "127.0.0.1"}
    resolvedor = lambda host, puerto: [ips[host]]
    visitas = []

    def manejar(request):
        visitas.append(str(request.url))
        if request.url.host == HOST_EJEMPLO and request.url.path == "/robots.txt":
            return httpx.Response(404)
        if request.url.host == HOST_EJEMPLO:
            return httpx.Response(302, headers={"location": "http://interno.example/secreto"})
        return httpx.Response(200, text="secreto", headers={"content-type": "text/html"})

    with pytest.raises(ErrorURL):
        leer_sitio(URL, resolvedor=resolvedor, transporte=httpx.MockTransport(manejar))
    assert not any("interno.example" in v for v in visitas)


def test_c5_robots_prohibe_el_acceso():
    transporte = transporte_de({"/robots.txt": "User-agent: *\nDisallow: /", "/": "<html></html>"})
    with pytest.raises(ErrorRobots) as e:
        leer_sitio(URL, resolvedor=resolvedor_publico, transporte=transporte)
    assert "robots.txt" in str(e.value)
    assert all(r.url.path == "/robots.txt" for r in transporte.peticiones)


def test_robots_excluye_rutas_concretas(paginas_ejemplo):
    paginas_ejemplo["/robots.txt"] = "User-agent: *\nDisallow: /contacto.html\n"
    paginas = leer_sitio(URL, resolvedor=resolvedor_publico, transporte=transporte_de(paginas_ejemplo))
    assert not any(p.url.endswith("/contacto.html") for p in paginas)


def test_c6_sitio_grande_devuelve_exactamente_20_paginas():
    enlaces = "".join(f'<a href="/p{i}.html">p{i}</a>' for i in range(60))
    paginas = {"/": f"<html><body>{enlaces}</body></html>"}
    paginas.update({f"/p{i}.html": f"<html><title>p{i}</title></html>" for i in range(60)})
    resultado = leer_sitio(URL, resolvedor=resolvedor_publico, transporte=transporte_de(paginas))
    assert len(resultado) == 20


def test_ignora_recursos_que_no_son_html(paginas_ejemplo):
    paginas_ejemplo["/"] = '<a href="/datos.json">d</a><a href="/horarios.html">h</a>'
    transporte = httpx.MockTransport(lambda r: (
        httpx.Response(200, text="{}", headers={"content-type": "application/json"}) if r.url.path == "/datos.json"
        else transporte_de(paginas_ejemplo).handle_request(r)))
    paginas = leer_sitio(URL, resolvedor=resolvedor_publico, transporte=transporte)
    assert not any(p.url.endswith("datos.json") for p in paginas)


def test_la_pagina_de_inicio_que_no_es_html_es_error_de_sitio():
    transporte = transporte_de({"/": "{}"}, tipo="application/json")
    with pytest.raises(ErrorSitio):
        leer_sitio(URL, resolvedor=resolvedor_publico, transporte=transporte)


def test_resolvedor_real_traduce_error_de_dns(monkeypatch):
    def falla(*a, **k):
        raise socket.gaierror("no resuelve")

    monkeypatch.setattr(socket, "getaddrinfo", falla)
    with pytest.raises(ErrorSitio):
        lector.resolvedor_dns("no-existe.invalid", 443)


def test_en_produccion_conecta_a_la_ip_comprobada_y_conserva_el_nombre(monkeypatch):
    """Sin transporte simulado, la petición va a la IP ya resuelta, con Host y SNI originales."""
    vistas = []

    class Falso(httpx.BaseTransport):
        def handle_request(self, request):
            vistas.append(request)
            return httpx.Response(200, text="<html></html>", headers={"content-type": "text/html"})

    monkeypatch.setattr(lector.httpx, "HTTPTransport", Falso)
    leer_sitio(URL, resolvedor=resolvedor_publico)
    pagina = [r for r in vistas if r.url.path == "/"][0]
    assert pagina.url.host == "93.184.216.34"
    assert pagina.headers["host"] == HOST_EJEMPLO
    assert pagina.extensions["sni_hostname"] == HOST_EJEMPLO
