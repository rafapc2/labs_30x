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

## Estado

En planificación. Ninguna tarea está implementada todavía. El primer paso es TASK-001, el andamiaje con `docker compose up`.
