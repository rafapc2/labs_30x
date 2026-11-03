# Progreso de la implementación

Nota viva. Se actualiza al cerrar cada tarea. El estado oficial está en Linear (proyecto «App MCP gemela para ChatGPT»); el mapa de IDs, en `linear-publish.yaml`.

| Tarea | Linear | Estado | Pendiente humano |
|---|---|---|---|
| 001 Andamiaje | TES-5 | Hecha | |
| 014 Formato del ZIP | TES-6 | Hecha (ADR 0003) | |
| 002 Esquema de base de datos | TES-7 | Hecha | |
| 004 Lectura segura de URLs | TES-8 | Hecha | |
| 003 Autenticación | TES-9 | Código y pruebas hechos | Registrar la app OAuth en GitHub o Google, poner credenciales en `.env`, probar un inicio de sesión real |
| 005 Extracción de contenido | TES-10 | Hecha | |
| 006 Metadata con el modelo | TES-11 | Código y pruebas hechos | Definir `OPENAI_API_KEY`; comprobar que `gpt-5-nano` admite JSON; revisar la calidad a mano |
| 008 Herramientas | TES-12 | Hecha | |
| 007 `POST /api/apps` | TES-13 | Hecha | |
| 009 Servidor MCP multi-app | TES-14 | Hecha (probada también en el contenedor) | |
| 010 Verificación de propiedad | TES-15 | Hecha | |
| 011 Simulador | TES-16 | Código y pruebas hechos | Revisión manual con el modelo real (`OPENAI_API_KEY`) |
| 016 Interfaz base | TES-17 | Hecha (ADR 0004) | |
| 012 Despliegue y retiro | TES-18 | Hecha | |
| 013 Panel de uso | TES-19 | Hecha | |
| 015 Paquete de publicación | TES-20 | Hecha | Subir el primer ZIP al panel de OpenAI para confirmar el formato |
| 017 Túnel y demo | TES-21 | **No iniciada la parte con efectos**: README, guion y `ngrok.yml.example` listos | Cuenta y dominio de ngrok, confirmar que se abre el túnel, cuenta de ChatGPT con servidores MCP personalizados |
| 018 Aceptación de extremo a extremo | TES-22 | Hecha | |

Decisiones de implementación que no estaban en la spec:

- Python 3.13 fijado (`.python-version`); la máquina trae 3.15, que no se usa para evitar ruedas ausentes.
- Las pruebas corren contra el PostgreSQL real del compose (puerto 5433 del host), en la base `gemela_test`.
- El lector recibe el transporte HTTP y el resolvedor DNS como parámetros. En pruebas se usa `httpx.MockTransport` y un resolvedor falso; en producción no hay ninguna opción que permita direcciones locales.
- Migraciones SQL simples (`migraciones/*.up.sql` y `.down.sql`) con un ejecutor propio en `gemela/db.py`, en lugar de Alembic.
- Se añadió la tabla `uso_simulador` (cuenta mensajes por cuenta, sin texto) para el límite por hora de S13.

- Servidor MCP: el gestor de sesiones del SDK solo arranca una vez, así que se crea en cada ciclo de vida de la app; la ruta `/apps/{id}/mcp` es ASGI directa y el manejador lee la app de `request.scope["path_params"]`. `TestClient` soporta el streaming (SSE), no hizo falta el plan B de S16.
- Modelo por defecto `gpt-5-nano` (el más barato de la tabla de precios de OpenAI del 2026-11-03), configurable con `MODELO_LLM`.
- `POST /api/apps` hace el análisis en un hilo con plazo de 120 s y solo escribe en la base de datos al terminar, en una transacción: un fallo o un plazo vencido no deja filas.
- Los intentos fallidos de crear una app no cuentan para el límite de 5 por hora; solo las apps creadas.
- Interfaz: plantillas Jinja2 en el servidor (ADR 0004). El «no envía la petición» de la prueba de interfaz se cumple porque el servidor responde el error sin llamar al lector ni al modelo.
- El contenedor `api` aplica las migraciones al arrancar (`python -m gemela.db`).
- Suite: `uv run pytest` en `ejercicios/`, con el PostgreSQL del compose levantado.
