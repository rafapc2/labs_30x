# ADR 0004: interfaz HTML renderizada en el servidor

- Estado: aceptada.
- Fecha: 2026-11-03.

## Contexto

La spec dejó abierta la tecnología de la interfaz sobre FastAPI (por ejemplo plantillas con HTMX o un front separado). La interfaz tiene cuatro vistas simples y es una demo.

## Decisión

Plantillas Jinja2 renderizadas por FastAPI, con CSS en la propia plantilla base y un poco de JavaScript sin dependencias solo donde hace falta (simulador, verificar, desplegar y retirar, que llaman a la API con `fetch`). Sin paso de compilación ni front aparte.

## Consecuencias

- Un solo servicio y una sola imagen; no hay que mantener un front ni un proceso de compilación.
- El formulario de URL se valida en el navegador (`type="url"` y `required`) y otra vez en el servidor. Si la URL es inválida, el servidor responde con el error junto al campo **sin llamar al lector ni al modelo**; eso es lo que significa «no envía la petición» en la prueba de interfaz.
- Las plantillas escapan el HTML por defecto: el contenido generado por el modelo a partir de sitios ajenos no se interpreta como código (hay una prueba).
- Las acciones POST de la interfaz usan JSON con `fetch`, y la cookie de sesión es `SameSite=Lax`, lo que limita las peticiones desde otros sitios.
- Si la interfaz crece, habrá que reconsiderarlo.
