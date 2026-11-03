"""Configuración leída del entorno. Nada de claves en el código."""
import os


def _env(nombre: str, defecto: str = "") -> str:
    return os.environ.get(nombre, defecto)


DATABASE_URL = _env("DATABASE_URL", "postgresql://gemela:gemela@localhost:5433/gemela")
SECRETO_SESION = _env("SECRETO_SESION", "solo-para-desarrollo")
URL_BASE = _env("URL_BASE", "http://localhost:8000")
URL_MCP_PUBLICA = _env("URL_MCP_PUBLICA", "http://localhost:8001")
OPENAI_API_KEY = _env("OPENAI_API_KEY")
MODELO_LLM = _env("MODELO_LLM")
GITHUB_CLIENT_ID = _env("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = _env("GITHUB_CLIENT_SECRET")
GOOGLE_CLIENT_ID = _env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _env("GOOGLE_CLIENT_SECRET")
TOPE_CARACTERES_MODELO = int(_env("TOPE_CARACTERES_MODELO", "30000"))
# Modelo más económico según la tabla de precios de OpenAI (consultada el 2026-11-03). Se cambia con MODELO_LLM.
MODELO_LLM_POR_DEFECTO = "gpt-5-nano"
PLAZO_ANALISIS = float(_env("PLAZO_ANALISIS", "120"))
MAX_APPS_POR_HORA = int(_env("MAX_APPS_POR_HORA", "5"))
MAX_MENSAJES_SIMULADOR_POR_HORA = int(_env("MAX_MENSAJES_SIMULADOR_POR_HORA", "30"))
