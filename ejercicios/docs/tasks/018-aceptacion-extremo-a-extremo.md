---
id: TASK-018
title: Pruebas de aceptación de extremo a extremo
milestone: "M4: Paquete, panel y demo"
priority: 3
estimate: 3
blockedBy: [TASK-012, TASK-013, TASK-016]
blocks: []
areas:
  - testing
parent: null
---

## Summary

Escribir las pruebas que comprueban de punta a punta los tres criterios de aceptación de la spec.

## Scope

### In scope

- Criterio 1: URL válida produce una app con las tres herramientas.
- Criterio 2: tras verificar y confirmar, la URL MCP responde la misma lista de herramientas.
- Criterio 3: tras llamar una herramienta, el panel cuenta la llamada.

### Out of scope

- Pruebas de calidad del modelo real, que se revisan a mano.

## Deliverables

- `tests/aceptacion/` con una prueba por criterio.
- Instrucción en el README para ejecutarlas.

## Acceptance Criteria

- [ ] Las tres pruebas pasan con el modelo simulado y el sitio de ejemplo.
- [ ] Se ejecutan con `pytest` sin pasos manuales.

## Test Plan

- `pytest tests/aceptacion`.

## Context

- Spec sección 4.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-012, TASK-013, TASK-016.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Sin notas adicionales.
