---
id: TASK-014
title: Investigar el formato del ZIP de envío a ChatGPT
milestone: "M4: Paquete, panel y demo"
priority: 2
estimate: 2
blockedBy: []
blocks: [TASK-015]
areas:
  - package
  - research
parent: null
---

## Summary

Averiguar la estructura exacta del ZIP que se sube al panel de OpenAI y registrar la decisión.

## Scope

### In scope

- Leer la documentación oficial de envío y de formato de plugins.
- Documentar estructura de archivos, campos obligatorios y límites.
- Actualizar la sección 6.10 de la spec.

### Out of scope

- Generar el ZIP (tarea 015).

## Deliverables

- `docs/decisions/0003-formato-zip-envio.md`.
- Cambios en la sección 6.10 de la spec.

## Acceptance Criteria

- [ ] La decisión describe la estructura del ZIP y cita las fuentes.
- [ ] Se indica si el formato Codex mencionado en la guía aplica a una app MCP.
- [ ] La spec 6.10 queda coherente con lo encontrado.

## Test Plan

- Revisión de la decisión por una segunda persona.

## Context

- Spec Q6 y 6.10.
- Guía oficial: https://developers.openai.com/apps-sdk/deploy/submission
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Puede empezar en cualquier momento. Conviene hacerla pronto: define el alcance de la tarea 015.
