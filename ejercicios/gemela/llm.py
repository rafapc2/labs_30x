"""Acceso al modelo de lenguaje. El modelo se elige con MODELO_LLM, sin tocar código."""
import json
from collections.abc import Callable

from gemela import config


class ErrorModelo(Exception):
    """El modelo falló o devolvió algo inutilizable (la API responde 502)."""


def nombre_modelo() -> str:
    return config.MODELO_LLM or config.MODELO_LLM_POR_DEFECTO


class ModeloOpenAI:
    """Pide una respuesta JSON al modelo. Nunca envía herramientas: el modelo que analiza sitios ajenos no tiene efectos."""

    def __init__(self, cliente=None):
        if cliente is None:
            from openai import OpenAI

            if not config.OPENAI_API_KEY:
                raise ErrorModelo("Falta OPENAI_API_KEY en el entorno")
            cliente = OpenAI(api_key=config.OPENAI_API_KEY, timeout=90.0)
        self._cliente = cliente

    def json(self, sistema: str, usuario: str) -> dict:
        try:
            r = self._cliente.chat.completions.create(
                model=nombre_modelo(),
                messages=[{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
                response_format={"type": "json_object"},
            )
            return json.loads(r.choices[0].message.content)
        except ErrorModelo:
            raise
        except Exception as e:  # red, límite, JSON roto: todo es un fallo del modelo para la API
            raise ErrorModelo(f"El modelo no respondió bien: {e.__class__.__name__}") from e


    def conversar(self, sistema: str, mensaje: str, definiciones: list[dict], ejecutor) -> tuple[str, str | None]:
        """Chat con herramientas para el simulador. Devuelve (respuesta, primera herramienta invocada o None).

        `definiciones`: [{"nombre", "descripcion", "esquema"}]. `ejecutor(nombre, argumentos)` ejecuta una herramienta.
        """
        herramientas = [{"type": "function", "function": {"name": d["nombre"], "description": d["descripcion"],
                         "parameters": d["esquema"]}} for d in definiciones]
        mensajes = [{"role": "system", "content": sistema}, {"role": "user", "content": mensaje}]
        try:
            r = self._cliente.chat.completions.create(model=nombre_modelo(), messages=mensajes, tools=herramientas)
            msg = r.choices[0].message
            usada = None
            if msg.tool_calls:
                mensajes.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
                    {"id": t.id, "type": "function", "function": {"name": t.function.name, "arguments": t.function.arguments}}
                    for t in msg.tool_calls]})
                for t in msg.tool_calls:
                    usada = usada or t.function.name
                    try:
                        salida = json.dumps(ejecutor(t.function.name, json.loads(t.function.arguments or "{}")), ensure_ascii=False)
                    except Exception as e:  # el error vuelve al modelo como texto, como lo vería ChatGPT
                        salida = f"Error: {e}"
                    mensajes.append({"role": "tool", "tool_call_id": t.id, "content": salida})
                msg = self._cliente.chat.completions.create(model=nombre_modelo(), messages=mensajes).choices[0].message
            return (msg.content or "").strip(), usada
        except ErrorModelo:
            raise
        except Exception as e:
            raise ErrorModelo(f"El modelo no respondió bien: {e.__class__.__name__}") from e


class ModeloSimulado:
    """Modelo para pruebas: devuelve una respuesta fija o calculada, y registra las llamadas."""

    def __init__(self, respuesta: dict | Callable[[str, str], dict] | None = None, eleccion=None):
        self._respuesta = respuesta
        self._eleccion = eleccion  # (nombre, argumentos) o función del mensaje, para `conversar`
        self.llamadas: list[tuple[str, str]] = []

    def conversar(self, sistema, mensaje, definiciones, ejecutor):
        self.llamadas.append((sistema, mensaje))
        eleccion = self._eleccion(mensaje) if callable(self._eleccion) else self._eleccion
        if isinstance(eleccion, Exception):
            raise eleccion
        if not eleccion:
            return "[simulado] sin herramienta", None
        nombre, argumentos = eleccion
        return f"[simulado] {json.dumps(ejecutor(nombre, argumentos), ensure_ascii=False)}", nombre

    def json(self, sistema: str, usuario: str) -> dict:
        self.llamadas.append((sistema, usuario))
        r = self._respuesta(sistema, usuario) if callable(self._respuesta) else self._respuesta
        if isinstance(r, Exception):
            raise r
        return r
