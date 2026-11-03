"""Las tres herramientas de cada app (solo lectura, BR-MCP-04).

El simulador y el servidor MCP usan estas mismas funciones, no copias.
"""
import re

MAX_FRAGMENTOS = 5
MAX_CARACTERES_FRAGMENTO = 500
MAX_TERMINOS = 20

DEFINICIONES = {
    "buscar": {
        "type": "object",
        "properties": {"consulta": {"type": "string", "description": "Lo que se quiere saber del sitio, en lenguaje natural."}},
        "required": ["consulta"],
    },
    "contacto": {"type": "object", "properties": {}},
    "listar_paginas": {"type": "object", "properties": {}},
}


class ErrorHerramienta(ValueError):
    """Herramienta desconocida o argumentos inválidos."""


def _terminos(consulta: str) -> list[str]:
    vistos = []
    for t in re.findall(r"\w{3,}", (consulta or "").lower()):
        if t not in vistos:
            vistos.append(t)
    return vistos[:MAX_TERMINOS]


def _fragmento(texto: str, terminos: list[str]) -> str:
    bajo = texto.lower()
    # Prefijos para tolerar plurales y conjugaciones ("horario" encuentra "horarios").
    posiciones = [bajo.find(t[:5]) for t in terminos if bajo.find(t[:5]) >= 0]
    inicio = max(min(posiciones) - 100, 0) if posiciones else 0
    return texto[inicio : inicio + MAX_CARACTERES_FRAGMENTO].strip()


def buscar(conn, app_id, consulta: str) -> list[dict]:
    """Hasta 5 fragmentos de 500 caracteres, con su URL, por relevancia (texto completo de PostgreSQL)."""
    terminos = _terminos(consulta)
    if not terminos:
        return []
    filas = conn.execute(
        "SELECT url, titulo, texto, ts_rank(tsv, q) AS relevancia "
        "FROM contenido, to_tsquery('spanish', %s) AS q "
        "WHERE app_id = %s AND tsv @@ q ORDER BY relevancia DESC, id LIMIT %s",
        (" | ".join(terminos), app_id, MAX_FRAGMENTOS),
    ).fetchall()
    return [{"url": f["url"], "titulo": f["titulo"], "fragmento": _fragmento(f["texto"], terminos)} for f in filas]


def contacto(conn, app_id) -> dict:
    fila = conn.execute("SELECT contacto FROM apps WHERE id = %s", (app_id,)).fetchone()
    base = {"correos": [], "telefonos": [], "direcciones": []}
    return {**base, **(fila["contacto"] if fila else {})}


def listar_paginas(conn, app_id) -> list[dict]:
    filas = conn.execute("SELECT titulo, url FROM contenido WHERE app_id = %s ORDER BY id", (app_id,)).fetchall()
    return [{"titulo": f["titulo"], "url": f["url"]} for f in filas]


def ejecutar(conn, app_id, nombre: str, argumentos: dict | None = None):
    """Punto único de entrada para el simulador y el servidor MCP."""
    argumentos = argumentos or {}
    if nombre == "buscar":
        consulta = argumentos.get("consulta")
        if not isinstance(consulta, str):
            raise ErrorHerramienta("buscar necesita el argumento 'consulta' de tipo texto")
        return buscar(conn, app_id, consulta)
    if nombre == "contacto":
        return contacto(conn, app_id)
    if nombre == "listar_paginas":
        return listar_paginas(conn, app_id)
    raise ErrorHerramienta(f"Herramienta desconocida: {nombre}")
