---
id: TASK-006
title: Generación de metadata con el modelo de lenguaje
milestone: "M2: Análisis y generación"
priority: 3
estimate: 5
blockedBy: [TASK-005]
blocks: [TASK-007, TASK-015]
areas:
  - llm
parent: null
---

## Summary

Generar nombre, descripciones y descripciones de las tres herramientas a partir del contenido, con el modelo más económico de OpenAI configurable.

## Scope

### In scope

- Cliente de OpenAI con el modelo en `MODELO_LLM`.
- Prompt que produce nombre, descripción corta, descripción larga, categoría y descripciones de `buscar`, `contacto` y `listar_paginas`.
- Respetar los límites: nombre y descripción corta de 30 caracteres como máximo, descripción larga de 4000.
- Modelo simulado para las pruebas.

### Out of scope

- Metadata del paquete de publicación (tarea 015) más allá de los campos que se generan aquí.

## Deliverables

- Módulo `generador`.
- Modelo simulado con respuestas fijas.

## Acceptance Criteria

- [ ] Con el modelo simulado, la salida incluye nombre, descripción y las tres herramientas.
- [ ] El nombre y la descripción corta nunca superan 30 caracteres (C15).
- [ ] Cambiar `MODELO_LLM` no requiere cambios de código.
- [ ] El modelo que analiza no recibe herramientas con efectos.

## Test Plan

- Prueba C15 y prueba de estructura con el modelo simulado.
- Revisión manual de calidad con el modelo real sobre un sitio verdadero.

## Context

- Spec 6.1 (modelo), Q1 y S12.
- Riesgo asumido: un modelo barato puede dar metadata más floja.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-005.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

El nombre exacto del modelo se fija aquí, al implementar.
