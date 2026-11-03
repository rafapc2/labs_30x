---
id: TASK-016
title: Interfaz base: inicio de sesión y formulario de URL
milestone: "M2: Análisis y generación"
priority: 3
estimate: 3
blockedBy: [TASK-003, TASK-007]
blocks: [TASK-018]
areas:
  - ui
parent: null
---

## Summary

Crear la interfaz web base con el inicio de sesión y el formulario donde se pega la URL, con el error junto al campo.

## Scope

### In scope

- Pantalla de inicio de sesión.
- Formulario de URL con el error de validación junto al campo y sin enviar la petición si es inválida.
- Tecnología de la interfaz: elegir al implementar (por ejemplo plantillas con HTMX) y registrarlo.

### Out of scope

- Vistas del simulador, paquete y panel (tareas 011, 013 y 015).

## Deliverables

- Plantillas o front elegido.
- Registro de la decisión de interfaz.

## Acceptance Criteria

- [ ] Con una URL inválida el formulario muestra el error junto al campo y no envía la petición.
- [ ] Con una URL válida se muestra el resultado del análisis.
- [ ] Sin sesión se redirige al inicio de sesión.

## Test Plan

- Prueba de interfaz de la URL inválida.

## Context

- Spec 6.7 y la prueba de interfaz de 6.6.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-003, TASK-007.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

La tecnología de interfaz era una pregunta abierta; decidirla aquí.
