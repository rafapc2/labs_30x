---
id: TASK-013
title: Panel básico de uso
milestone: "M4: Paquete, panel y demo"
priority: 3
estimate: 3
blockedBy: [TASK-003, TASK-009]
blocks: [TASK-018]
areas:
  - panel
  - ui
parent: null
---

## Summary

Mostrar al dueño llamadas por día, por herramienta, errores y fecha de la última llamada.

## Scope

### In scope

- `GET /api/apps/{id}/panel`.
- Vista del panel en la interfaz.
- Acceso solo de la cuenta dueña (BR-MCP-07).

### Out of scope

- Texto o identidad de quien consulta; analítica avanzada.

## Deliverables

- Router y vista del panel.

## Acceptance Criteria

- [ ] Tras una llamada a una herramienta de una app desplegada, el contador de esa herramienta aumenta (C11).
- [ ] Una llamada con error suma un error y no guarda el texto (C12).
- [ ] Otra cuenta recibe 404 (C18).

## Test Plan

- Pruebas C11, C12 y C18.

## Context

- Spec 6.3 y BR-MCP-05.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-003, TASK-009.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Sin notas adicionales.
