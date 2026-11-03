---
id: TASK-007
title: Endpoint POST /api/apps
milestone: "M2: Análisis y generación"
priority: 2
estimate: 3
blockedBy: [TASK-003, TASK-005, TASK-006]
blocks: [TASK-010, TASK-011, TASK-016]
areas:
  - api
parent: null
---

## Summary

Orquestar lector, extractor y generador en `POST /api/apps`, con token de verificación, tiempo máximo y límite por cuenta.

## Scope

### In scope

- Crear la app en borrador y devolver `id`, `nombre`, `descripcion`, `herramientas` y `token_verificacion`.
- Tiempo máximo de 120 segundos; si se supera, 502 y no queda una app a medias.
- Límite de 5 apps por hora por cuenta (429).
- Errores 422 y 502 según la spec.

### Out of scope

- Verificación, simulador, despliegue y retiro.

## Deliverables

- Router `apps` con el endpoint.
- Contador de creaciones por cuenta.

## Acceptance Criteria

- [ ] Con el sitio de ejemplo devuelve 200 con nombre, descripción y herramientas (C1).
- [ ] La respuesta incluye `token_verificacion` (C22).
- [ ] La sexta creación en una hora devuelve 429 (C20).
- [ ] Un fallo a mitad del análisis no deja filas en la base.

## Test Plan

- Pruebas C1, C20 y C22.
- Prueba de limpieza ante fallo.

## Context

- Spec 6.3, 6.5 (rendimiento y abuso).
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-003, TASK-005, TASK-006.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

El análisis es síncrono; en local es aceptable.
