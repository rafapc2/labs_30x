---
id: TASK-010
title: Verificación de propiedad del sitio
milestone: "M3: Simulador, verificación y despliegue MCP"
priority: 3
estimate: 3
blockedBy: [TASK-004, TASK-007]
blocks: [TASK-012]
areas:
  - verification
parent: null
---

## Summary

Comprobar que el dueño controla el sitio con el token en una etiqueta `meta` o en un archivo `/.well-known/`.

## Scope

### In scope

- `POST /api/apps/{id}/verificacion`.
- Buscar `<meta name="mcp-gemela" content="TOKEN">` en la página de inicio o `/.well-known/mcp-gemela.txt`.
- 409 si no se encuentra o si el token es de otra app.
- Reutilizar el bloqueo de direcciones privadas del lector.

### Out of scope

- Despliegue (tarea 012).

## Deliverables

- Router y lógica de verificación.

## Acceptance Criteria

- [ ] Con la etiqueta presente la app queda verificada (C8).
- [ ] Sin la etiqueta responde 409 (C9).
- [ ] Un token de otra app falla con 409 (C22).
- [ ] La comprobación aplica el mismo bloqueo de direcciones privadas (C4).

## Test Plan

- Pruebas C8, C9 y C22 contra el fixture.

## Context

- Spec S3, S7, BR-MCP-03 y 6.5 («Seguridad al leer URLs»).
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-004, TASK-007.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Sin notas adicionales.
