---
id: TASK-004
title: Lectura segura de URLs
milestone: "M2: Análisis y generación"
priority: 2
estimate: 5
blockedBy: [TASK-001]
blocks: [TASK-005, TASK-010]
areas:
  - analysis
  - security
parent: null
---

## Summary

Construir el lector de sitios: validación de la URL, bloqueo de direcciones privadas, `robots.txt`, límite de páginas y un sitio de ejemplo para pruebas.

## Scope

### In scope

- Validación de la URL: `http` o `https` y dominio público (BR-MCP-01).
- Bloqueo de direcciones privadas, locales y de metadatos de nube, comprobado al abrir la conexión y en las redirecciones.
- Respeto de `robots.txt` (BR-MCP-06).
- Máximo de 20 páginas del mismo dominio (BR-MCP-02).
- Un sitio estático de ejemplo, servido como fixture.

### Out of scope

- Extracción del contenido útil (tarea 005) y contenido dinámico o con sesión.

## Deliverables

- Módulo `lector` con función que devuelve las páginas descargadas.
- Fixture del sitio de ejemplo en `tests/fixtures/`.

## Acceptance Criteria

- [ ] Una URL sin `http` o `https` se rechaza con 422 (C2).
- [ ] Un dominio que no responde produce el error que la API traducirá a 502 (C3).
- [ ] Una URL que resuelve a una dirección privada se rechaza sin hacer la petición (C4).
- [ ] Un `robots.txt` que prohíbe el acceso detiene el análisis con el motivo (C5).
- [ ] Un sitio de más de 20 páginas devuelve exactamente 20 (C6).

## Test Plan

- Pruebas C2 a C6 contra el fixture.

## Context

- Spec 6.4 (BR-MCP-01, 02, 06) y 6.5 («Seguridad al leer URLs»).
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-001.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

El mismo bloqueo se reutiliza en la verificación de propiedad (tarea 010).
