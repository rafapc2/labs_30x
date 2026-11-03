"""Acceso a PostgreSQL y migraciones SQL simples (subir y revertir)."""
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from gemela import config

CARPETA_MIGRACIONES = Path(__file__).resolve().parent.parent / "migraciones"


def conectar(url: str | None = None) -> psycopg.Connection:
    """Conexión con filas como diccionarios. Quien la usa decide cuándo confirmar."""
    return psycopg.connect(url or config.DATABASE_URL, row_factory=dict_row)


def _versiones() -> list[str]:
    return sorted(p.name.split(".")[0] for p in CARPETA_MIGRACIONES.glob("*.up.sql"))


def _asegurar_tabla(conn: psycopg.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migraciones (version TEXT PRIMARY KEY)")


def aplicadas(conn: psycopg.Connection) -> list[str]:
    _asegurar_tabla(conn)
    return [r["version"] for r in conn.execute("SELECT version FROM schema_migraciones ORDER BY version")]


def aplicar(conn: psycopg.Connection) -> list[str]:
    """Aplica las migraciones pendientes. Devuelve las versiones aplicadas ahora."""
    hechas = set(aplicadas(conn))
    nuevas = []
    for version in _versiones():
        if version in hechas:
            continue
        conn.execute((CARPETA_MIGRACIONES / f"{version}.up.sql").read_text(encoding="utf-8"))
        conn.execute("INSERT INTO schema_migraciones (version) VALUES (%s)", (version,))
        nuevas.append(version)
    conn.commit()
    return nuevas


def revertir(conn: psycopg.Connection, pasos: int = 1) -> list[str]:
    """Revierte las últimas `pasos` migraciones aplicadas."""
    revertidas = []
    for version in reversed(aplicadas(conn)[-pasos:] if pasos else []):
        conn.execute((CARPETA_MIGRACIONES / f"{version}.down.sql").read_text(encoding="utf-8"))
        conn.execute("DELETE FROM schema_migraciones WHERE version = %s", (version,))
        revertidas.append(version)
    conn.commit()
    return revertidas


if __name__ == "__main__":
    with conectar() as c:
        print("aplicadas:", aplicar(c))
