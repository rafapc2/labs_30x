# App MCP gemela para ChatGPT

Una web que recibe la URL pública de un sitio y genera una app MCP gemela que se puede conectar a ChatGPT, para que el dueño del negocio esté donde su cliente ya está. Es una demo del programa AI for Developers de 30X.

## Problema

Los dueños de sitios web no tienen presencia dentro de ChatGPT, donde sus clientes empiezan cada vez más a buscar y a actuar, y tampoco saben cuánto se usa esa presencia.

## Qué hace

1. El dueño inicia sesión con Google o GitHub y pega la URL de su sitio.
2. Opcionalmente verifica que es el dueño.
3. El sistema analiza el sitio y genera la app y su metadata.
4. Un simulador de ChatGPT permite probarla.
5. El sistema la despliega por MCP y entrega el paquete de publicación y la guía.
6. Un panel muestra cuánto se usa.

El envío al directorio de ChatGPT no se automatiza: OpenAI solo lo admite desde su panel. Lo hace el dueño con el paquete generado.

## Arquitectura en una línea

La app gemela son datos en PostgreSQL servidos por un servidor MCP genérico, expuesto por un túnel; la interfaz y la API quedan solo en local. Detalle en [docs/architecture.md](docs/architecture.md).

## Stack

Python, FastAPI, PostgreSQL, SDK de MCP para Python, OpenAI, Docker Compose y ngrok.

## Documentación

- [Spec de la rebanada](docs/spec-mcp-gemela.md) y [su evaluación](docs/spec-review.md).
- [Plan de tareas](docs/tasks/milestones.md).
- [Decisiones](docs/decisions/).
- [Skills usadas](skills/README.md).

## Puesta en marcha

Requisitos: Docker con Compose, y `uv` con Python 3.13 para las pruebas.

```bash
cp .env.example .env      # y completa los valores (ver abajo)
docker compose up --build # interfaz en http://localhost:8000, servidor MCP en http://localhost:8001
```

La interfaz (puerto 8000) **nunca** debe exponerse a Internet; solo el servidor MCP (puerto 8001) se expone, por el túnel.

### Variables de `.env`

| Variable | Para qué |
|---|---|
| `OPENAI_API_KEY` | Análisis del sitio y simulador. Sin ella, crear una app responde 502 con el motivo. |
| `MODELO_LLM` | Modelo de OpenAI. Si está vacía se usa `gpt-5-nano`, el más barato de la tabla de precios consultada el 2026-11-03. Hay que comprobar con una llamada real que admite salida JSON y herramientas. |
| `SECRETO_SESION` | Firma de la cookie de sesión. Pon una cadena larga y aleatoria. |
| `URL_BASE` | URL de la interfaz, para los retornos OAuth. Con `https://` la cookie sale con `Secure`. |
| `URL_MCP_PUBLICA` | URL pública del servidor MCP (la del túnel). |
| `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` | Inicio de sesión con GitHub. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Inicio de sesión con Google. |

Con las credenciales de **uno** de los dos proveedores basta.

### Registrar la aplicación OAuth

- **GitHub:** Settings → Developer settings → OAuth Apps → New OAuth App. URL de retorno: `http://localhost:8000/auth/github/callback`.
- **Google:** Google Cloud Console → APIs y servicios → Credenciales → ID de cliente de OAuth (aplicación web). URI de redirección: `http://localhost:8000/auth/google/callback`.

Copia el identificador y el secreto a `.env` y reinicia.

## Pruebas

```bash
docker compose up -d postgres   # las pruebas usan el PostgreSQL real, en la base gemela_test
uv sync
uv run pytest                   # todas
uv run pytest tests/aceptacion  # los tres criterios de aceptación de la spec
```

Las pruebas usan un sitio de ejemplo (`tests/fixtures/`), red simulada y un modelo simulado: no necesitan Internet ni claves. La calidad real de la metadata y de las respuestas del simulador se revisa a mano.

## Demo con ChatGPT

Requiere cuentas propias: ChatGPT con acceso a servidores MCP personalizados (modo de desarrollador) y ngrok.

1. `docker compose up --build` y entra en `http://localhost:8000`.
2. Inicia sesión, pega la URL de un sitio **que controles** y espera el análisis (hasta 2 minutos).
3. Prueba la app en el simulador. Es una aproximación de ChatGPT, no ChatGPT.
4. Verifica la propiedad: pon en tu sitio la etiqueta `meta` o el archivo `/.well-known/mcp-gemela.txt` que indica la página, y pulsa «Verificar ahora».
5. Pulsa «Desplegar».
6. Expón **solo el puerto 8001**: copia `ngrok.yml.example` a `ngrok.yml`, pon tu dominio estático y tu token, y ejecuta `ngrok start --all --config ngrok.yml`. Pon la URL pública en `URL_MCP_PUBLICA` y reinicia.
7. En ChatGPT: Plugins → «Add custom MCP server» → URL `https://TU-DOMINIO/apps/<id>/mcp`. Debe listar las tres herramientas.
8. Pregunta algo sobre el sitio y mira el panel de uso.
9. Comprueba que la interfaz no es accesible por el túnel: `curl https://TU-DOMINIO/api/apps` debe dar 404.

El envío al directorio de ChatGPT no se automatiza: usa la página «Paquete de publicación» y sigue su guía.

## Limitaciones conocidas

- El simulador es una aproximación.
- El análisis es una petición síncrona de hasta 120 segundos.
- El túnel de la demo no sustituye el punto HTTPS permanente que exige el envío al directorio.
- El formato del ZIP se basa en la guía de OpenAI y no se ha subido a su panel todavía.

## Estado

Implementado y probado: las 18 tareas del plan, salvo lo que depende de pasos humanos (credenciales y cuentas). El estado exacto, tarea por tarea, está en [docs/tasks/progreso.md](docs/tasks/progreso.md).
