---
id: TASK-003
title: Autenticación con Google o GitHub
milestone: "M1: Cimientos y autenticación"
priority: 2
estimate: 5
blockedBy: [TASK-001, TASK-002]
blocks: [TASK-007, TASK-013, TASK-016]
areas:
  - auth
parent: null
---

## Summary

Implementar el inicio de sesión por OAuth, la sesión por cookie y el control de acceso por cuenta.

## Scope

### In scope

- Rutas `GET /auth/{proveedor}/login`, `GET /auth/{proveedor}/callback` y `POST /auth/logout`.
- Parámetro `state` generado y validado.
- Cookie `HttpOnly`, `SameSite=Lax` y `Secure` con HTTPS.
- Dependencia de FastAPI que exige sesión en `/api/*` (401) y devuelve 404 si la app es de otra cuenta.
- Funciona al menos con un proveedor; el otro se agrega con la misma estructura.

### Out of scope

- Correo y contraseña, roles, equipos y recuperación de cuenta.

## Deliverables

- Módulo `auth`.
- Registro de la cuenta en la tabla `usuarios` en el primer inicio de sesión.
- Instrucciones en el README para registrar la aplicación OAuth con la URL de retorno local.

## Acceptance Criteria

- [ ] Un endpoint `/api/*` sin sesión responde 401 (C17).
- [ ] Una cuenta que pide una app ajena recibe 404 (C18).
- [ ] Un proveedor no admitido responde 404 (C19).
- [ ] Un retorno con `state` distinto se rechaza y no crea sesión (C26).
- [ ] Solo se guardan proveedor, identificador y nombre.

## Test Plan

- Pruebas C17, C18, C19 y C26 con el proveedor simulado.
- Prueba manual del inicio de sesión real con un proveedor.

## Context

- Spec 6.1 (autenticación), 6.3 (contrato), 6.5 (sesión), S14.
- Depende del esquema de la tarea 002.
- Spec completa: `ejercicios/docs/spec-mcp-gemela.md`.
- Tareas previas: TASK-001, TASK-002.

## Definition of Ready

- [ ] Los supuestos de la conversación previa están escritos en la spec.
- [ ] Los archivos, documentos y dependencias necesarios están referenciados arriba.
- [ ] Un agente de código podría empezar sin contexto adicional.

## Notes

Registrar la aplicación en Google o GitHub es un paso humano: el agente no puede obtener las credenciales. Dejarlo documentado.
