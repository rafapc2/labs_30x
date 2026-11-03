---
id: TASK-012
title: Despliegue y retiro de apps
milestone: "M3: Simulador, verificación y despliegue MCP"
priority: 2
estimate: 3
blockedBy: [TASK-009, TASK-010]
blocks: [TASK-015, TASK-017, TASK-018]
areas:
  - deploy
parent: null
---

## Summary

Activar una app verificada para que responda por MCP y permitir retirarla.

## Scope

### In scope

- `POST /api/apps/{id}/despliegue`: 403 si no está verificada; devuelve la URL MCP.
- `POST /api/apps/{id}/retiro`: pasa a retirada; el servidor MCP responde 404.
- Transiciones de estado válidas (BR-MCP-09).

### Out of scope

- La URL pública del túnel (tarea 017).

## Deliverables

- Router de despliegue y retiro.

## Acceptance Criteria

- [ ] Despliegue sin verificación responde 403 (C7).
- [ ] Despliegue de una app verificada devuelve la URL MCP, que responde la misma lista de herramientas del simulador (C10).
- [ ] Tras el retiro, la lista de herramientas MCP responde 404 (C21).

## Test Plan

- Pruebas C7, C10 y C21.

## Context

- Spec 6.3, BR-MCP-03, BR-MCP-09, S8 y S11.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-009, TASK-010.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Sin notas adicionales.
