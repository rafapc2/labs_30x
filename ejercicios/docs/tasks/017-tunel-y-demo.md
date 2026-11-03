---
id: TASK-017
title: Túnel ngrok y guion de la demo con ChatGPT
milestone: "M4: Paquete, panel y demo"
priority: 3
estimate: 3
blockedBy: [TASK-009, TASK-012]
blocks: []
areas:
  - deploy
  - docs
parent: null
---

## Summary

Exponer solo el servidor MCP con ngrok y documentar la demo de punta a punta, conectando la app en ChatGPT en modo de desarrollador.

## Scope

### In scope

- Configurar ngrok con dominio estático solo sobre el puerto de `mcp`.
- Confirmar los límites vigentes del plan gratuito de ngrok.
- Conectar la app en ChatGPT por «Add custom MCP server» y comprobar que lista las herramientas.
- Guion de demo en el README.

### Out of scope

- Despliegue permanente y envío al directorio.

## Deliverables

- Configuración de ngrok.
- Guion de demo.

## Acceptance Criteria

- [ ] La interfaz web y la API no son accesibles por la URL del túnel.
- [ ] ChatGPT lista las tres herramientas de la app desplegada.
- [ ] El guion permite repetir la demo desde cero.

## Test Plan

- Comprobación manual: `curl` a la URL del túnel hacia `/api/apps` falla; ChatGPT lista las herramientas.

## Context

- Spec Q2, 6.5 y 6.10.
- Requiere que el plan de ChatGPT permita servidores MCP personalizados; es una condición que hay que comprobar.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-009, TASK-012.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Pasos humanos: crear la cuenta de ngrok y usar una cuenta de ChatGPT con acceso a servidores personalizados.
