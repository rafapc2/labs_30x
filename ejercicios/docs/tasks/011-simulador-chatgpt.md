---
id: TASK-011
title: Simulador de ChatGPT
milestone: "M3: Simulador, verificación y despliegue MCP"
priority: 3
estimate: 5
blockedBy: [TASK-007, TASK-008]
blocks: []
areas:
  - simulator
  - ui
parent: null
---

## Summary

Chat que usa el modelo con las herramientas de la app para mostrar cómo respondería y qué herramienta invoca.

## Scope

### In scope

- `POST /api/apps/{id}/simulador` que devuelve respuesta y herramienta invocada.
- Vista de chat en la interfaz.
- Límite de 30 mensajes por hora por cuenta (S13).
- Aviso visible de que es una aproximación (S4).

### Out of scope

- Reproducir el aspecto o la lógica de selección de ChatGPT real.

## Deliverables

- Router del simulador.
- Vista de chat.

## Acceptance Criteria

- [ ] Un mensaje sobre un dato del sitio recibe respuesta e indica la herramienta invocada (C13).
- [ ] El mensaje 31 en una hora responde 429 (C24).
- [ ] Usa las funciones de la tarea 008, no una copia.

## Test Plan

- Pruebas C13 y C24 con el modelo simulado.
- Revisión manual con el modelo real.

## Context

- Spec 6.2 (simulador), S4 y S13.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-007, TASK-008.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Funciona sin verificación (BR-MCP-03).
