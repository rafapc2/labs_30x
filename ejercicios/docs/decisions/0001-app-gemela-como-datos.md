# ADR 0001: la app gemela son datos, no código generado

- Estado: aceptada.
- Fecha: 2026-11-02.

## Contexto

Cada sitio analizado debe terminar como una app MCP que ChatGPT pueda llamar. Se puede generar código y lanzar un servicio por sitio, o guardar el contenido y la definición de herramientas y servirlos desde un servidor común.

## Decisión

Guardar el contenido y las herramientas en PostgreSQL y servirlos con un único servidor MCP genérico. Desplegar una app es activar sus filas.

## Consecuencias

- Desplegar y retirar son cambios de estado, rápidos y fáciles de probar.
- No hay un contenedor ni un proceso por sitio.
- Las tres herramientas son fijas; no se admiten herramientas a medida por sitio en esta versión.
- Todas las apps comparten el mismo servidor: un fallo del servidor afecta a todas.
