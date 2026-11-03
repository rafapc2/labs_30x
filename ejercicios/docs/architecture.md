# Arquitectura

Resumen de la sección 6 de [spec-mcp-gemela.md](spec-mcp-gemela.md), que es la fuente de verdad.

## Componentes

| Componente | Responsabilidad | Se expone por el túnel |
|---|---|---|
| `api` (FastAPI) | Interfaz web, autenticación, generación, verificación, simulador, despliegue, paquete y panel | No |
| `mcp` | Servidor MCP genérico que atiende `/apps/{id}/mcp` | **Sí, es el único** |
| `postgres` | Usuarios, apps, contenido, herramientas y llamadas | No |
| OpenAI | Modelo de lenguaje para analizar y para el simulador | Salida de datos |

## Flujo de datos

```
Dueño ──> api ──> lector seguro ──> sitio del dueño
              └─> extractor ──> postgres
              └─> generador ──> OpenAI ──> metadata
Dueño ──> api ──> simulador ──> herramientas ──> postgres
ChatGPT ──> túnel ──> mcp ──> herramientas ──> postgres
Dueño ──> api ──> panel ──> postgres (llamadas)
```

## Modelo de datos

- `usuarios`: proveedor, identificador en el proveedor, nombre.
- `apps`: usuario, URL, nombre, descripción, estado (borrador, desplegada, retirada), verificada, token de verificación.
- `contenido`: app, URL, título, texto. Con índice de texto completo.
- `herramientas`: app, nombre, descripción, tipo.
- `llamadas`: app, herramienta, fecha, resultado. Nunca el texto de la consulta.

## Herramientas de cada app

| Herramienta | Parámetros | Resultado |
|---|---|---|
| `buscar` | `consulta` | Hasta 5 fragmentos de 500 caracteres con su URL, por relevancia |
| `contacto` | ninguno | Correo, teléfono y dirección extraídos |
| `listar_paginas` | ninguno | Título y URL de cada página analizada |

## Seguridad

- Lectura de URLs ajenas con bloqueo de direcciones privadas, comprobado al abrir la conexión, y respeto de `robots.txt`.
- Cada app pertenece a una cuenta; el acceso ajeno responde 404.
- El túnel expone solo el puerto de `mcp`.
- La ruta MCP es pública por diseño y solo expone contenido público del sitio.

## Elecciones y razones

- **Datos y no código generado:** desplegar es activar filas, sin construir un contenedor por sitio. Ver [ADR 0001](decisions/0001-app-gemela-como-datos.md).
- **Servidor MCP en su propio puerto:** un túnel expone un puerto completo. Ver [ADR 0002](decisions/0002-servidor-mcp-puerto-aparte.md).
- **Transporte:** HTTP en streaming en una ruta `/mcp`, según la [guía de conexión de OpenAI](https://developers.openai.com/apps-sdk/deploy/connect-chatgpt).
- **Sin Kong ni otro gateway:** la versión actual llama a OpenAI directamente.

## Límites conocidos

- El simulador es una aproximación de ChatGPT, no ChatGPT.
- El análisis es una petición síncrona de hasta 120 segundos.
- El túnel de la demo no sustituye el punto de conexión HTTPS permanente que exige el envío al directorio.
