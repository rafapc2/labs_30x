"""Lector seguro de sitios (BR-MCP-01, 02 y 06).

Toda petición a una URL dada por un usuario pasa por `TransporteSeguro`, que resuelve el
dominio y bloquea direcciones no públicas justo antes de abrir cada conexión, también en
cada redirección. En producción conecta a la IP ya comprobada, así que un cambio de
resolución entre la comprobación y la conexión no lo elude. El transporte y el resolvedor
son inyectables para poder probar sin red y sin permitir direcciones locales en producción.
"""
import ipaddress
import socket
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

AGENTE = "GemelaBot"
MAX_PAGINAS = 20
MAX_BYTES_PAGINA = 1_000_000
MAX_REDIRECCIONES = 5

Resolvedor = Callable[[str, int], list[str]]


class ErrorURL(ValueError):
    """La URL no es válida o no está permitida (la API responde 422)."""


class ErrorRobots(ErrorURL):
    """El sitio prohíbe el acceso en su robots.txt (la API responde 422 con el motivo)."""


class ErrorSitio(Exception):
    """El sitio no responde o falla (la API responde 502)."""


@dataclass
class Pagina:
    url: str
    html: str


def resolvedor_dns(host: str, puerto: int) -> list[str]:
    try:
        info = socket.getaddrinfo(host, puerto, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise ErrorSitio(f"No se pudo resolver el dominio {host}") from e
    return sorted({i[4][0] for i in info})


def _ip_permitida(texto: str) -> bool:
    ip = ipaddress.ip_address(texto)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def validar_url(url: str) -> str:
    """BR-MCP-01: `http` o `https` y un dominio. La comprobación de que sea público se hace al conectar."""
    url = (url or "").strip()
    partes = urlparse(url)
    if partes.scheme not in ("http", "https"):
        raise ErrorURL("La URL debe empezar con http:// o https://")
    if not partes.hostname:
        raise ErrorURL("La URL no tiene un dominio")
    if len(url) > 2000:
        raise ErrorURL("La URL es demasiado larga")
    try:
        partes.port
    except ValueError as e:
        raise ErrorURL("La URL tiene un puerto inválido") from e
    try:
        if not _ip_permitida(partes.hostname):
            raise ErrorURL("La URL apunta a una dirección que no es pública")
    except ValueError:
        pass  # no es una IP literal: es un nombre de dominio
    return url


def comprobar_destino(host: str, puerto: int, resolvedor: Resolvedor) -> list[str]:
    """Resuelve el dominio y rechaza si alguna dirección no es pública."""
    ips = resolvedor(host, puerto)
    if not ips:
        raise ErrorSitio(f"No se pudo resolver el dominio {host}")
    for ip in ips:
        if not _ip_permitida(ip):
            raise ErrorURL("La URL apunta a una dirección que no es pública")
    return ips


class TransporteSeguro(httpx.BaseTransport):
    def __init__(self, resolvedor: Resolvedor, interno: httpx.BaseTransport | None = None):
        self._resolvedor = resolvedor
        self._fijar_ip = interno is None  # con un transporte simulado no hay DNS que fijar
        self._interno = interno or httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host
        puerto = request.url.port or (443 if request.url.scheme == "https" else 80)
        ips = comprobar_destino(host, puerto, self._resolvedor)
        if self._fijar_ip:
            cabeceras = dict(request.headers)
            cabeceras["host"] = request.url.netloc.decode("ascii")
            extensiones = dict(request.extensions)
            extensiones["sni_hostname"] = host
            request = httpx.Request(
                request.method, request.url.copy_with(host=ips[0]), headers=cabeceras,
                stream=request.stream, extensions=extensiones,
            )
        return self._interno.handle_request(request)

    def close(self) -> None:
        self._interno.close()


def crear_cliente(resolvedor: Resolvedor | None = None, transporte: httpx.BaseTransport | None = None,
                  timeout: float = 10.0) -> httpx.Client:
    return httpx.Client(
        transport=TransporteSeguro(resolvedor or resolvedor_dns, transporte),
        follow_redirects=True, max_redirects=MAX_REDIRECCIONES,
        timeout=timeout, headers={"User-Agent": f"{AGENTE}/1.0"},
    )


def _descargar_html(cliente: httpx.Client, url: str) -> str | None:
    """Descarga una página HTML. Devuelve None si no es HTML o no es una respuesta exitosa."""
    try:
        with cliente.stream("GET", url) as r:
            if r.status_code >= 400:
                return None
            if "html" not in r.headers.get("content-type", "").lower():
                return None
            trozos, total = [], 0
            for trozo in r.iter_bytes():
                total += len(trozo)
                trozos.append(trozo)
                if total >= MAX_BYTES_PAGINA:
                    break
            return b"".join(trozos)[:MAX_BYTES_PAGINA].decode(r.encoding or "utf-8", errors="replace")
    except (ErrorURL, ErrorSitio):
        raise
    except httpx.HTTPError as e:
        raise ErrorSitio(f"El sitio no responde: {e.__class__.__name__}") from e


def _robots(cliente: httpx.Client, url: str) -> RobotFileParser:
    p = urlparse(url)
    rp = RobotFileParser()
    try:
        r = cliente.get(f"{p.scheme}://{p.netloc}/robots.txt")
        if r.status_code in (401, 403):
            rp.disallow_all = True
        elif r.status_code >= 400:
            rp.allow_all = True
        else:
            rp.parse(r.text.splitlines())
    except httpx.HTTPError:
        rp.allow_all = True
    return rp


def _normalizar(url: str) -> str:
    url, _ = urldefrag(url)
    p = urlparse(url)
    return p._replace(path=p.path or "/").geturl()


def _enlaces(html: str, base: str, host: str) -> list[str]:
    salida = []
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        destino = urljoin(base, a["href"].strip())
        p = urlparse(destino)
        if p.scheme in ("http", "https") and p.hostname == host:
            salida.append(_normalizar(destino))
    return salida


def leer_sitio(url: str, *, resolvedor: Resolvedor | None = None,
               transporte: httpx.BaseTransport | None = None, max_paginas: int = MAX_PAGINAS) -> list[Pagina]:
    """Descarga hasta `max_paginas` páginas HTML del mismo dominio, empezando por `url`."""
    inicio = _normalizar(validar_url(url))
    host = urlparse(inicio).hostname
    paginas: list[Pagina] = []
    with crear_cliente(resolvedor, transporte) as cliente:
        robots = _robots(cliente, inicio)
        if not robots.can_fetch(AGENTE, inicio):
            raise ErrorRobots("El sitio prohíbe el acceso automático en su robots.txt")
        pendientes, vistas = [inicio], {inicio}
        while pendientes and len(paginas) < max_paginas:
            actual = pendientes.pop(0)
            html = _descargar_html(cliente, actual)
            if html is None:
                if actual == inicio:
                    raise ErrorSitio("La página de inicio no devolvió HTML")
                continue
            paginas.append(Pagina(actual, html))
            for enlace in _enlaces(html, actual, host):
                if enlace not in vistas and robots.can_fetch(AGENTE, enlace):
                    vistas.add(enlace)
                    pendientes.append(enlace)
    return paginas
