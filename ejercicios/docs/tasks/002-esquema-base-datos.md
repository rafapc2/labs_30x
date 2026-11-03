---
id: TASK-002
title: Esquema de base de datos y migraciones
milestone: "M1: Cimientos y autenticación"
priority: 2
estimate: 3
blockedBy: [TASK-001]
blocks: [TASK-003, TASK-005, TASK-008]
areas:
  - db
parent: null
---

## Summary

Crear las tablas `usuarios`, `apps`, `contenido`, `herramientas` y `llamadas` con migraciones, y el índice de búsqueda de texto completo.

## Scope

### In scope

- Migraciones (por ejemplo con Alembic) para las cinco tablas del modelo de datos de la spec.
- Estados de `apps`: borrador, desplegada, retirada.
- Campo `token_verificacion` en `apps`.
- Índice de texto completo en `contenido`.

### Out of scope

- Datos de ejemplo y lógica de acceso más allá de lo necesario para probar el esquema.

## Deliverables

- Migraciones.
- Módulo de acceso a datos con las operaciones básicas.

## Acceptance Criteria

- [ ] Las migraciones se aplican sobre una base vacía y se pueden revertir.
- [ ] `llamadas` no tiene ninguna columna para el texto de la consulta.
- [ ] Existe un índice de texto completo sobre el texto de `contenido`.

## Test Plan

- Prueba que aplica y revierte las migraciones.
- Prueba que inserta un contenido y lo encuentra con una consulta de texto completo.

## Context

- Spec 6.2, «Modelo de datos mínimo».
- Spec BR-MCP-05: el panel no guarda el texto de las consultas.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-001.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

El servicio `postgres` de la aplicación es el único; no hay base de datos de Kong en esta versión.
