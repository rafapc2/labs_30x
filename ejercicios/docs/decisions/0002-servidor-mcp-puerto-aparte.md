# ADR 0002: el servidor MCP corre en su propio puerto

- Estado: aceptada.
- Fecha: 2026-11-02.

## Contexto

La demo necesita que ChatGPT llegue al servidor MCP desde Internet, y se usa un túnel de ngrok. Un túnel expone un puerto completo. La interfaz web y la API de generación incluyen endpoints que no deben ser públicos: creación, verificación, simulador y panel.

## Decisión

Ejecutar el servidor MCP como un servicio aparte, en su propio puerto, y exponer solo ese puerto por el túnel.

## Consecuencias

- Internet solo ve las herramientas de las apps desplegadas.
- Hay dos servicios que mantener y configurar.
- La ruta MCP es pública y sin autenticación por diseño, porque ChatGPT debe poder llamarla; solo expone contenido público del sitio.
- Para el envío al directorio hará falta un punto de conexión HTTPS permanente, que esta decisión no resuelve.
