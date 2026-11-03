---
id: TASK-015
title: Paquete de publicación y guía
milestone: "M4: Paquete, panel y demo"
priority: 3
estimate: 5
blockedBy: [TASK-006, TASK-012, TASK-014]
blocks: []
areas:
  - package
parent: null
---

## Summary

Generar el paquete con metadata, ocho casos de prueba, textos de privacidad y términos, y la guía paso a paso.

## Scope

### In scope

- `GET /api/apps/{id}/paquete`: 403 si no está verificada.
- Campos con sus límites: nombre y descripción corta de 30 caracteres, descripción larga de 4000.
- Exactamente cinco casos positivos con `tools_triggered` y `expected_behavior` y tres negativos.
- Textos de política de privacidad y de términos.
- Guía con el aviso del simulador y del plan de ChatGPT.
- Formato del ZIP según la tarea 014.

### Out of scope

- Envío al directorio, video, iconos y publicación de los textos en el sitio del dueño.

## Deliverables

- Generador del paquete.
- Vista del paquete en la interfaz.

## Acceptance Criteria

- [ ] El paquete incluye los campos de la sección 6.10, ocho casos de prueba y los textos (C14).
- [ ] Cada herramienta nombrada en los casos existe en la app (C14).
- [ ] Una descripción corta de más de 30 caracteres se acorta (C25).
- [ ] La guía lista lo que el dueño debe completar por su cuenta.

## Test Plan

- Pruebas C14 y C25.

## Context

- Spec 6.10 y S5.
- Decisión de la tarea 014.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-006, TASK-012, TASK-014.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

El envío lo hace el dueño desde la cuenta verificada de su organización.
