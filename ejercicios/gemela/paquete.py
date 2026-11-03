"""Paquete de publicación para el directorio de ChatGPT (spec 6.10, ADR 0003).

Se genera todo lo que se puede generar. Lo que solo el dueño puede aportar queda marcado con
`PENDIENTE` y la guía lo lista. Nada de esto se envía a OpenAI: el envío es manual.
"""
import io
import json
import re
import unicodedata
import zipfile
from urllib.parse import urlparse

from gemela.generador import MAX_CORTA, MAX_LARGA, MAX_NOMBRE, acortar

PENDIENTE = "PENDIENTE"


def slug(nombre: str) -> str:
    """Identificador del plugin: minúsculas, números y guiones simples, hasta 64 caracteres."""
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "-", sin_acentos.lower()).strip("-")
    return (base or "app-gemela")[:64].strip("-")


def casos_de_prueba(nombre: str, titulos: list[str], herramientas: set[str]) -> dict:
    """Exactamente cinco casos positivos y tres negativos, generados sin modelo para que sean verificables."""
    tema = titulos[0] if titulos else nombre
    otro = titulos[1] if len(titulos) > 1 else tema
    positivos = [
        ("Busca en el sitio de {n} información sobre «{t}».", ["buscar"], "Usa buscar y responde con datos del sitio, citando la página de origen."),
        ("¿Cómo puedo contactar con {n}?", ["contacto"], "Usa contacto y devuelve el correo, el teléfono o la dirección que el sitio publica."),
        ("¿Qué páginas tiene el sitio de {n}?", ["listar_paginas"], "Usa listar_paginas y enumera las páginas con su título y dirección."),
        ("Cuéntame lo que dice {n} sobre «{o}».", ["buscar"], "Usa buscar y resume solo lo que el sitio dice."),
        ("¿Tiene {n} un teléfono o un correo de contacto?", ["contacto"], "Usa contacto; si el sitio no publica el dato, lo dice sin inventarlo."),
    ]
    negativos = [
        ("Escribe un poema sobre el otoño.", "No usa la app: la petición no tiene relación con el sitio."),
        ("¿Cuánto es 15 por 12?", "No usa la app: es una pregunta de cálculo general."),
        (f"Haz una reserva o una compra en {nombre} y paga con mi tarjeta.", "No usa la app para comprar ni reservar: sus herramientas son solo de lectura."),
    ]
    return {
        "positive": [{"prompt": p.format(n=nombre, t=tema, o=otro), "tools_triggered": t, "expected_behavior": e}
                     for p, t, e in positivos if set(t) <= herramientas],
        "negative": [{"prompt": p, "expected_behavior": e} for p, e in negativos],
    }


def politica_privacidad(nombre: str, url_sitio: str) -> str:
    return f"""# Política de privacidad de la app «{nombre}»

_Plantilla generada automáticamente. Revísala y adáptala antes de publicarla._

**Qué hace la app.** Responde preguntas sobre el contenido público de {url_sitio} usando tres herramientas de solo lectura: buscar en el sitio, mostrar los datos de contacto y listar las páginas.

**Qué datos usa.** Solo el contenido que el sitio ya publica para cualquier visitante.

**Qué datos guarda.** Un contador de llamadas por herramienta, con fecha y si salió bien o mal. No guarda el texto de las preguntas ni de las respuestas, ni identifica a quien pregunta.

**Con quién se comparten.** Con nadie. La app no vende ni cede datos.

**Contacto.** {PENDIENTE}: correo o dirección donde se pueden hacer consultas sobre privacidad.
"""


def terminos(nombre: str, url_sitio: str) -> str:
    return f"""# Términos de servicio de la app «{nombre}»

_Plantilla generada automáticamente. Revísala y adáptala antes de publicarla._

1. La app ofrece información extraída del contenido público de {url_sitio}. Puede estar desactualizada o incompleta.
2. La app es de solo lectura: no realiza compras, reservas ni otras acciones en nombre del usuario.
3. La información no sustituye la que ofrece directamente el titular del sitio.
4. El titular puede retirar la app en cualquier momento.
5. Contacto: {PENDIENTE}.
"""


GUIA = [
    "Completa lo marcado como PENDIENTE: `developerName`, la URL de soporte, el contacto de la política de privacidad y los términos.",
    "Publica la política de privacidad y los términos en una URL HTTPS de tu propio sitio y anota esas URL (deben identificar al mismo editor que el envío).",
    "Prepara los iconos (cuadrados, de al menos 48×48 px, PNG, JPEG, WebP o SVG, hasta 5 MiB) y un video de demostración que los revisores puedan ver, y agrégalos al paquete.",
    "El túnel de la demo no basta para el envío: la URL del servidor MCP debe ser un punto HTTPS público y estable. Aloja el servidor MCP en un sitio permanente y actualiza `mcp.json`.",
    "Confirma en el panel de OpenAI la lista de categorías válidas; la categoría sugerida aquí la propuso un modelo.",
    "Verifica tu organización en OpenAI (individuo o empresa); solo el propietario o un miembro con el rol «Apps Management Write» puede enviar.",
    "Prueba antes en ChatGPT con el modo de desarrollador: «Add custom MCP server» con la URL que termina en `/mcp`. Tu plan o espacio de trabajo debe permitir servidores MCP personalizados.",
    "Recuerda que el simulador de esta herramienta es una aproximación: ChatGPT real puede elegir otras herramientas o responder distinto.",
    "Sube el ZIP desde el panel de OpenAI. Lo que la guía de OpenAI no cubre (estructura de carpeta raíz, contenido de la skill, errores de validación) se confirma al subirlo: corrige lo que el panel indique.",
]


def construir(app: dict, herramientas: list[dict], paginas: list[dict], url_mcp: str) -> dict:
    nombre = acortar(app["nombre"], MAX_NOMBRE)
    nombres = {h["nombre"] for h in herramientas}
    interfaz = {
        "displayName": nombre,
        "shortDescription": acortar(app["descripcion_corta"] or nombre, MAX_CORTA),
        "longDescription": acortar(app["descripcion_larga"] or app["descripcion"], MAX_LARGA),
        "developerName": PENDIENTE,
        "category": app["categoria"] or PENDIENTE,
        "websiteURL": app["url"],
        "supportURL": PENDIENTE,
        "privacyPolicyURL": PENDIENTE,
        "termsOfServiceURL": PENDIENTE,
    }
    casos = casos_de_prueba(nombre, [p["titulo"] for p in paginas if p["titulo"]], nombres)
    plugin = {
        "name": slug(nombre), "version": "1.0.0", "description": app["descripcion"],
        "extensions": {"com.openai": {
            "interface": interfaz,
            "review": {"test_cases": casos, "demo_recording_url": PENDIENTE},
        }},
    }
    mcp = {"mcpServers": {slug(nombre): {"type": "streamable-http", "url": url_mcp}}}
    return {
        "campos": interfaz, "casos_de_prueba": casos,
        "politica_privacidad": politica_privacidad(nombre, app["url"]), "terminos": terminos(nombre, app["url"]),
        "plugin_json": plugin, "mcp_json": mcp,
        "guia": GUIA,
        "pendiente_del_dueno": sorted(k for k, v in interfaz.items() if v == PENDIENTE) + ["iconos", "demo_recording_url"],
        "advertencias": ([] if urlparse(url_mcp).scheme == "https" else
                         ["La URL del servidor MCP no es HTTPS: sirve para probar en ChatGPT, no para el envío."]),
    }


def zip_bytes(paquete: dict, nombre_skill: str = "empezar") -> bytes:
    """ZIP con la disposición Agent Plugins. No referencia iconos (no existen aún): el dueño los añade."""
    plugin = paquete["plugin_json"]
    skill = (f"---\nname: {nombre_skill}\ndescription: Cómo usar la app {paquete['campos']['displayName']}.\n---\n\n"
             f"{paquete['campos']['longDescription']}\n\nHerramientas: " +
             ", ".join(f"`{n}`" for n in sorted({t for c in paquete['casos_de_prueba']['positive'] for t in c['tools_triggered']})) + ".\n")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("plugin.json", json.dumps(plugin, ensure_ascii=False, indent=2))
        z.writestr("mcp.json", json.dumps(paquete["mcp_json"], ensure_ascii=False, indent=2))
        z.writestr(f"skills/{nombre_skill}/SKILL.md", skill)
        z.writestr("LEEME.md", "# Paquete generado\n\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(paquete["guia"], 1)) + "\n")
        z.writestr("PRIVACIDAD.md", paquete["politica_privacidad"])
        z.writestr("TERMINOS.md", paquete["terminos"])
    return buffer.getvalue()
