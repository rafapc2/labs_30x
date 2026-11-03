# AGENTS.md

Contexto persistente para agentes de código que trabajan en este proyecto.

## Misión y alcance

Una web que recibe la URL pública de un sitio y genera una **app MCP gemela** que se conecta a ChatGPT. Incluye un simulador de ChatGPT, verificación de propiedad, despliegue, paquete de publicación y un panel básico de uso. Es una **demo**.

La fuente de verdad es [docs/spec-mcp-gemela.md](docs/spec-mcp-gemela.md). Si algo no está allí, es una pregunta, no una decisión.

## Restricciones no negociables

- Solo ChatGPT en esta versión. Claude queda fuera.
- La app gemela son **datos**, no código generado. Un servidor MCP genérico las sirve todas.
- Las herramientas son **de solo lectura** y son tres: `buscar`, `contacto` y `listar_paginas`. El simulador y el servidor MCP usan la misma implementación.
- El servidor MCP corre en **su propio puerto** y es lo único que se expone por el túnel. La interfaz web y la API nunca se exponen.
- Nunca se guarda el texto de las consultas que llegan a las herramientas ni el de las conversaciones del simulador. Solo contadores.
- Toda petición a una URL que da un usuario pasa por el lector seguro: bloqueo de direcciones privadas comprobado al conectar, `robots.txt`, máximo 20 páginas.
- Sin verificación de propiedad, una app solo se genera y se prueba en el simulador. No se despliega ni recibe paquete.
- Cada app pertenece a la cuenta que la creó. Una app ajena responde 404.
- No hay API de envío al directorio de ChatGPT. El envío lo hace el dueño desde su cuenta de OpenAI.

## Stack

Python, FastAPI, PostgreSQL, SDK oficial de MCP para Python, OpenAI (el modelo más económico, en `MODELO_LLM`), Docker Compose, `pytest`, ngrok con dominio estático para la demo.

## Comandos esperados

Se crean en TASK-001; confirmar que existen antes de usarlos.

```bash
docker compose up        # levanta api, mcp y postgres
pytest                   # todas las pruebas
pytest tests/aceptacion  # pruebas de los tres criterios
```

## Convenciones

- Documentación y mensajes de la interfaz en español. Nombres de código en español o inglés según el módulo, pero consistentes dentro de él.
- Sin claves en el repositorio. Variables en `.env`, plantilla en `.env.example`.
- Versiones de dependencias e imágenes fijadas; sin `latest`.
- Las pruebas usan un sitio de ejemplo como fixture y un modelo simulado. La calidad real del modelo se revisa a mano.
- No se impone TDD, pero cada tarea lista las pruebas que debe dejar en verde.

## Dónde mirar

- [docs/architecture.md](docs/architecture.md): componentes y flujo de datos.
- [docs/decisions/](docs/decisions/): decisiones de arquitectura.
- [docs/tasks/](docs/tasks/): plan de tareas, con `task-package.yaml` y `milestones.md`.
