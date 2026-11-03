"""Convierte las páginas descargadas en texto limpio, extrae el contacto y arma el texto para el modelo."""
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from gemela import config
from gemela.lector import Pagina

RE_CORREO = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
RE_TELEFONO = re.compile(r"(?<![\w@.])\+?\d[\d\s().-]{7,}\d(?!\w)")
RE_DIRECCION = re.compile(r"(?:Direcci[oó]n|Domicilio|Ubicaci[oó]n)\s*:\s*(.+?)(?:\.\s|\.$|$)", re.IGNORECASE)
MAX_POR_TIPO = 5


@dataclass
class PaginaExtraida:
    url: str
    titulo: str
    texto: str


@dataclass
class Analisis:
    paginas: list[PaginaExtraida]
    contacto: dict[str, list[str]] = field(default_factory=lambda: {"correos": [], "telefonos": [], "direcciones": []})


def _limpiar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def extraer_pagina(pagina: Pagina) -> PaginaExtraida:
    sopa = BeautifulSoup(pagina.html, "html.parser")
    titulo = _limpiar(sopa.title.get_text(" ")) if sopa.title else ""
    for etiqueta in sopa(["script", "style", "noscript", "template", "svg"]):
        etiqueta.decompose()
    return PaginaExtraida(pagina.url, titulo, _limpiar(sopa.get_text(" ")))


def _unicos(valores) -> list[str]:
    vistos, salida = set(), []
    for v in valores:
        clave = v.lower()
        if v and clave not in vistos:
            vistos.add(clave)
            salida.append(v)
    return salida[:MAX_POR_TIPO]


def extraer_contacto(paginas: list[Pagina]) -> dict[str, list[str]]:
    correos, telefonos, direcciones = [], [], []
    for pagina in paginas:
        sopa = BeautifulSoup(pagina.html, "html.parser")
        for a in sopa.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("mailto:"):
                correos.append(href[7:].split("?")[0])
            elif href.lower().startswith("tel:"):
                telefonos.append(_limpiar(href[4:]))
        for bloque in sopa.find_all("address"):
            direcciones.append(_limpiar(bloque.get_text(" ")))
        texto = _limpiar(sopa.get_text(" "))
        correos += RE_CORREO.findall(texto)
        for m in RE_TELEFONO.findall(texto):
            if 9 <= len(re.sub(r"\D", "", m)) <= 15:
                telefonos.append(_limpiar(m))
        direcciones += [_limpiar(m) for m in RE_DIRECCION.findall(texto)]
    # Si el sitio no publica un dato, la lista queda vacía: no se inventa.
    return {"correos": _unicos(correos), "telefonos": _unicos(telefonos), "direcciones": _unicos(direcciones)}


def analizar(paginas: list[Pagina]) -> Analisis:
    return Analisis([extraer_pagina(p) for p in paginas], extraer_contacto(paginas))


def texto_para_modelo(analisis: Analisis, tope: int | None = None) -> str:
    """Texto acotado que se envía al modelo (S12). Nunca supera `tope` caracteres."""
    tope = config.TOPE_CARACTERES_MODELO if tope is None else tope
    partes, usado = [], 0
    for p in analisis.paginas:
        bloque = f"## {p.titulo or p.url} ({p.url})\n{p.texto}\n\n"
        if usado + len(bloque) > tope:
            bloque = bloque[: max(tope - usado, 0)]
        if not bloque:
            break
        partes.append(bloque)
        usado += len(bloque)
        if usado >= tope:
            break
    return "".join(partes)


def guardar_contenido(conn, app_id, analisis: Analisis) -> None:
    """Una fila de `contenido` por página, y el contacto en la app."""
    import json

    for p in analisis.paginas:
        conn.execute(
            "INSERT INTO contenido (app_id, url, titulo, texto) VALUES (%s, %s, %s, %s)",
            (app_id, p.url, p.titulo, p.texto),
        )
    conn.execute("UPDATE apps SET contacto = %s WHERE id = %s", (json.dumps(analisis.contacto), app_id))
