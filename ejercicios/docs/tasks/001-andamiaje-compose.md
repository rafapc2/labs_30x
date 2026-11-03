---
id: TASK-001
title: Andamiaje del proyecto y Docker Compose
milestone: "M1: Cimientos y autenticación"
priority: 2
estimate: 3
blockedBy: []
blocks: [TASK-002, TASK-003, TASK-004]
areas:
  - infra
parent: null
---

## Summary

Crear la estructura del proyecto Python con FastAPI, un servicio MCP vacío en puerto aparte, PostgreSQL y `pytest`, todo arrancable con `docker compose up`.

## Scope

### In scope

- Estructura de carpetas, `pyproject.toml` y dependencias fijadas.
- Servicios `api` (FastAPI), `mcp` (puerto propio) y `postgres` en `docker-compose.yml`.
- Archivo `.env.example` con las variables: `MODELO_LLM`, `OPENAI_API_KEY`, credenciales OAuth, `DATABASE_URL`.
- Una ruta `GET /salud` en cada servicio.

### Out of scope

- Lógica de negocio, autenticación y esquema de base de datos.

## Deliverables

- `docker-compose.yml`, `Dockerfile`, `pyproject.toml`, `.env.example`.
- `tests/` con una prueba de humo.

## Acceptance Criteria

- [ ] `docker compose up` levanta los tres servicios sin errores.
- [ ] `GET /salud` responde 200 en `api` y en `mcp`.
- [ ] El servicio `mcp` escucha en un puerto distinto del de `api`.
- [ ] Ninguna clave aparece en el repositorio; `.env` está en `.gitignore`.

## Test Plan

- `docker compose up -d` y `curl` a ambos `/salud`.
- `pytest` ejecuta la prueba de humo en verde.

## Context

- Spec 6.1 (stack) y 6.2 (componentes).
- Spec 6.5, «Exposición por el túnel»: el puerto de `mcp` es el único que se expondrá.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Fijar versiones. No usar `latest` en imágenes.
