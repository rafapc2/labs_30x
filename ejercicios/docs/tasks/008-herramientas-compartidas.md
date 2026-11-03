---
id: TASK-008
title: Herramientas de la app: buscar, contacto y listar_paginas
milestone: "M3: Simulador, verificación y despliegue MCP"
priority: 2
estimate: 3
blockedBy: [TASK-002, TASK-005]
blocks: [TASK-009, TASK-011]
areas:
  - mcp
parent: null
---

## Summary

Implementar una sola vez las tres herramientas, que usarán el simulador y el servidor MCP.

## Scope

### In scope

- `buscar(consulta)`: hasta 5 fragmentos de 500 caracteres con su URL, por relevancia con texto completo de PostgreSQL.
- `contacto()`: datos extraídos.
- `listar_paginas()`: título y URL de cada página.
- Solo lectura (BR-MCP-04).

### Out of scope

- Exposición por MCP (tarea 009) y por el simulador (tarea 011).

## Deliverables

- Módulo `herramientas` con las tres funciones y su descripción de parámetros.

## Acceptance Criteria

- [ ] `buscar` devuelve como máximo 5 fragmentos de 500 caracteres cada uno, con URL de origen.
- [ ] `buscar` sin coincidencias devuelve una lista vacía y no falla (C23).
- [ ] Ninguna herramienta escribe en la base de datos de contenido.

## Test Plan

- Prueba C23 y pruebas de límites de `buscar`.

## Context

- Spec 6.2, tabla de herramientas, y S9.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-002, TASK-005.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

La misma implementación debe usarse en el simulador y en MCP.
