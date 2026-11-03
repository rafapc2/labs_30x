---
id: TASK-009
title: Servidor MCP multi-app
milestone: "M3: Simulador, verificación y despliegue MCP"
priority: 2
estimate: 5
blockedBy: [TASK-008]
blocks: [TASK-012, TASK-013, TASK-017]
areas:
  - mcp
parent: null
---

## Summary

Servir las herramientas de cada app en `/apps/{id}/mcp` con transporte HTTP en streaming y registrar cada llamada.

## Scope

### In scope

- Servidor con el SDK oficial de MCP para Python, en su propio puerto.
- Ruta `/apps/{id}/mcp` que expone las herramientas de la app a partir de sus datos.
- Registrar cada llamada en `llamadas` (herramienta, fecha, ok o error), sin el texto de la consulta.
- 404 para apps inexistentes, en borrador o retiradas.
- Investigar si `TestClient` soporta el streaming de MCP; si no, usar el cliente MCP del SDK (S16).

### Out of scope

- Despliegue y retiro de apps (tarea 012).

## Deliverables

- Módulo `servidor_mcp`.
- Prueba de integración del servidor.

## Acceptance Criteria

- [ ] La ruta responde con transporte HTTP en streaming y la lista de herramientas (C16).
- [ ] Una llamada con error se registra como error y no guarda el texto de la consulta (C12).
- [ ] Una app retirada responde 404 (C21).
- [ ] Solo este servicio queda pensado para exponerse por el túnel.

## Test Plan

- Pruebas C12 y C16, con la alternativa de S16 si hace falta.
- Comprobación manual con MCP Inspector.

## Context

- Spec 6.1 (estándar), 6.2 (servidor MCP), BR-MCP-08, Q3 y S10, S16.
- Guía de conexión de OpenAI: https://developers.openai.com/apps-sdk/deploy/connect-chatgpt
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-008.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

La ruta es pública por diseño (BR-MCP-08): solo expone contenido público del sitio.
