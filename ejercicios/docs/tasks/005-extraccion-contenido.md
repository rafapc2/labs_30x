---
id: TASK-005
title: Extracción y almacenamiento del contenido
milestone: "M2: Análisis y generación"
priority: 3
estimate: 3
blockedBy: [TASK-002, TASK-004]
blocks: [TASK-006, TASK-007, TASK-008]
areas:
  - analysis
parent: null
---

## Summary

Convertir las páginas descargadas en texto limpio, extraer los datos de contacto y guardarlos, respetando el tope de caracteres para el modelo.

## Scope

### In scope

- Extraer título y texto de cada página.
- Extraer correo, teléfono y dirección para la herramienta `contacto`.
- Guardar en `contenido` y en la app.
- Tope de 30 000 caracteres enviados al modelo por app (S12), documentado y configurable.

### Out of scope

- Generación de metadata con el modelo (tarea 006).

## Deliverables

- Módulo `extractor`.
- Función que arma el texto acotado para el modelo.

## Acceptance Criteria

- [ ] Para el sitio de ejemplo, `contenido` queda con una fila por página.
- [ ] Los datos de contacto del sitio de ejemplo se extraen correctamente.
- [ ] El texto que se prepara para el modelo nunca supera el tope.

## Test Plan

- Pruebas sobre el fixture: filas guardadas, contacto extraído, tope respetado.

## Context

- Spec 6.2 (herramientas `contacto` y `buscar`), S9 y S12.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-002, TASK-004.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Si el sitio no publica contacto, el resultado queda vacío; no se inventa.
