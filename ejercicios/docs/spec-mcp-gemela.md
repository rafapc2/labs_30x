# Spec de la rebanada: app MCP gemela de un sitio web para ChatGPT

## 1. Problema

Los dueños de sitios web no tienen presencia dentro de ChatGPT, donde sus clientes empiezan cada vez más a buscar y a actuar, y tampoco saben cuánto se usa esa presencia. Pierden la oportunidad de estar donde está su cliente.

**Éxito de la rebanada (demo):** un dueño pega la URL de su sitio y en una sola sesión ve su app funcionando en un simulador de ChatGPT, la deja desplegada y consulta cuánto se usa.

## 2. Usuario

El dueño de un negocio con sitio web público que quiere que sus clientes lo encuentren y usen desde ChatGPT, sin escribir código.

## 3. El flujo, paso a paso

1. El dueño inicia sesión con Google o GitHub y pega la URL pública de su sitio.
2. Opcionalmente, verifica que es el dueño con una etiqueta o un archivo en su sitio.
3. El sistema analiza el sitio y genera el contenido de la app y la metadata para ChatGPT.
4. El sistema abre un simulador de ChatGPT, donde el dueño conversa con la app y ve cómo respondería y qué herramienta invoca.
5. El dueño confirma, y el sistema genera la MCP app y la despliega en una URL pública. El despliegue exige haber verificado la propiedad (paso 2).
6. El sistema entrega el paquete de publicación y la guía para conectarla en ChatGPT y enviarla al directorio.
7. El dueño ve el panel básico de uso.

## 4. Criterios de aceptación

- [ ] Al pegar una URL pública válida, el simulador muestra una app con nombre, descripción y las tres herramientas (`buscar`, `contacto` y `listar_paginas`), con descripciones generadas a partir del contenido del sitio.
- [ ] Tras verificar la propiedad y confirmar, la app queda en una URL pública que responde a la lista de herramientas MCP con las mismas herramientas que mostró el simulador.
- [ ] Después de llamar a una herramienta de una app desplegada, el panel muestra esa llamada en el contador de su herramienta.

## 5. Qué queda fuera

Claude como plataforma, envío automático al directorio de ChatGPT, sitios con inicio de sesión o contenido dinámico, acciones como comprar o reservar, cobros, registro con correo y contraseña, roles y equipos, edición manual de las herramientas generadas y registro del texto de las conversaciones.

## 6. Decisiones técnicas

### 6.1 Stack decidido

- Lenguaje: Python.
- API web: FastAPI.
- Base de datos: PostgreSQL.
- Autenticación: inicio de sesión con Google o GitHub mediante OAuth 2.0 (OpenID Connect en el caso de Google). Sesión con cookie en la interfaz web.
- Modelo de lenguaje: OpenAI, siempre el modelo más económico disponible. Se configura con la variable de entorno `MODELO_LLM`; el nombre exacto se fija al implementar.
- Estándar de la app: servidor MCP con transporte HTTP en streaming (*streamable HTTP*) en una ruta que termina en `/mcp`, según la [guía de conexión de OpenAI](https://developers.openai.com/apps-sdk/deploy/connect-chatgpt).
- Despliegue de la demo: ejecución local con Docker Compose; el servidor MCP se expone a ChatGPT con un túnel gratuito de ngrok con dominio estático (Q2).

### 6.2 Arquitectura propuesta

La app «gemela» no es código generado. Es **datos** (contenido del sitio y definición de herramientas) guardados en PostgreSQL y servidos por un servidor MCP genérico. Así desplegar una app es crear sus filas y activarla, no construir ni lanzar un contenedor por sitio.

| Componente | Responsabilidad |
|---|---|
| Interfaz web | Formulario de URL, verificación opcional, simulador y panel. La sirve FastAPI. Solo escucha en local; nunca pasa por el túnel. |
| Autenticación | Inicio de sesión con Google o GitHub, sesión por cookie y control de acceso: cada app pertenece a la cuenta que la creó. |
| API de generación | Valida la URL, lee el sitio, extrae el contenido y genera la metadata y las herramientas con un modelo de lenguaje. |
| Servidor MCP | Un servicio aparte, en su propio puerto, que atiende `/apps/{id}/mcp` y expone las herramientas de cada app a partir de sus datos. Implementado con el SDK oficial de MCP para Python. Es lo único que se expone por el túnel. |
| Simulador | Un chat que usa un modelo de lenguaje con las herramientas de la app para mostrar cómo respondería y qué herramienta invocaría. |
| PostgreSQL | Guarda los usuarios, las apps, el contenido extraído, las herramientas y las llamadas. |

Separar el servidor MCP de la interfaz web es deliberado: un túnel expone un puerto completo, y así Internet solo ve las herramientas de las apps y no los endpoints de creación, verificación ni panel.

Herramientas generadas (solo lectura, tres, S9). El simulador y el servidor MCP usan la misma implementación de cada una:

| Herramienta | Parámetros | Resultado |
|---|---|---|
| `buscar` | `consulta`: texto | Hasta 5 fragmentos de 500 caracteres como máximo, cada uno con su URL de origen, ordenados por relevancia con la búsqueda de texto completo de PostgreSQL. Lista vacía si no hay coincidencias. |
| `contacto` | ninguno | Los datos de contacto extraídos durante el análisis (correo, teléfono, dirección). Vacío si el sitio no los publica. |
| `listar_paginas` | ninguno | Título y URL de cada página analizada. |

Modelo de datos mínimo:
- `usuarios`: id, proveedor (Google o GitHub), identificador en el proveedor, nombre, fecha. No se guarda contraseña.
- `apps`: id, usuario, URL, nombre, descripción, estado (borrador, desplegada, retirada), verificada (sí o no), token de verificación, fecha.
- `contenido`: app, URL de la página, título, texto.
- `herramientas`: app, nombre, descripción, tipo.
- `llamadas`: app, herramienta, fecha, resultado (ok o error). No guarda el contenido de la consulta.

**Diferencias de la implementación respecto de este modelo** (detalle en [progreso.md](tasks/progreso.md)): `apps` tiene además `descripcion_corta`, `descripcion_larga`, `categoria` y `contacto`; hay una sexta tabla, `uso_simulador` (cuenta mensajes por cuenta para el límite de S13, sin texto); las migraciones son SQL simples en `migraciones/`.

### 6.3 Contrato de la API

- `GET /auth/{proveedor}/login`, `GET /auth/{proveedor}/callback` y `POST /auth/logout`, con `proveedor` igual a `google` o `github`.
- Todos los endpoints `/api/*` exigen sesión: sin sesión responden 401. Si la app existe pero es de otra cuenta, responden 404 (no se revela que existe).
- `POST /api/apps` con `{ "url": string }`: crea una app en borrador, analiza el sitio y devuelve `{ "id", "nombre", "descripcion", "herramientas": [...], "token_verificacion" }`. El token es aleatorio, único por app y ligado a la app y a la cuenta. Responde 422 si la URL no es válida y 502 si el sitio no responde.
- `POST /api/apps/{id}/verificacion`: comprueba la etiqueta o el archivo y marca la app como verificada. Responde 409 si no se encuentra.
- `POST /api/apps/{id}/simulador` con `{ "mensaje": string }`: devuelve la respuesta y la herramienta invocada.
- `POST /api/apps/{id}/retiro`: pasa la app a estado retirada. El servidor MCP responde 404 para una app retirada.
- `POST /api/apps/{id}/despliegue`: activa la app y devuelve su URL MCP. Responde 403 si la app no está verificada.
- `GET /api/apps/{id}/paquete`: devuelve el paquete de publicación (ver 6.10). Responde 403 si no está verificada.
- `GET /api/apps/{id}/panel`: devuelve llamadas por día, por herramienta, errores y fecha de la última llamada.

Códigos adicionales de la implementación: la verificación responde 422 si el sitio resuelve a una dirección no pública y 502 si no responde; el retiro responde 409 si la app no está desplegada; el simulador responde 422 con un mensaje vacío o de más de 2000 caracteres y 429 pasados 30 mensajes por hora; `GET /api/apps/{id}/paquete.zip` descarga el ZIP del [ADR 0003](decisions/0003-formato-zip-envio.md). La interfaz sigue el [ADR 0004](decisions/0004-interfaz-html-en-servidor.md).

### 6.4 Reglas de negocio

- BR-MCP-01: la URL debe ser `http` o `https` y tener un dominio público.
- BR-MCP-02: solo se analizan páginas del mismo dominio, hasta 20 páginas, con el contenido que un visitante sin sesión puede ver.
- BR-MCP-03: sin verificar, la app se puede generar y probar en el simulador, pero no desplegar ni recibir el paquete de publicación.
- BR-MCP-04: las herramientas son de solo lectura; nunca ejecutan acciones en el sitio.
- BR-MCP-05: el panel solo cuenta llamadas; no guarda el texto de las consultas.
- BR-MCP-06: el analizador respeta el `robots.txt` del sitio; si prohíbe el acceso, no se genera la app.
- BR-MCP-07: cada app pertenece a la cuenta que la creó; solo esa cuenta puede verificarla, probarla en el simulador, desplegarla, ver su paquete y su panel.
- BR-MCP-08: la ruta MCP de una app desplegada es pública y no pide autenticación, porque ChatGPT debe poder llamarla; solo expone el contenido público del sitio.
- BR-MCP-09: el dueño puede retirar una app desplegada en cualquier momento; una app retirada deja de responder por MCP y no vuelve a desplegarse sin repetir el despliegue.

### 6.5 Restricciones no funcionales

- **Seguridad al leer URLs:** el sistema hace peticiones a direcciones que da un usuario, así que bloquea las que resuelvan a direcciones privadas, locales o de metadatos de nube, y no sigue redirecciones hacia ellas. El bloqueo se aplica también a la comprobación de verificación y se verifica al abrir la conexión, no solo al validar la URL, para que una redirección o un cambio de resolución no lo eludan. El modelo que analiza sitios ajenos no tiene herramientas con efectos: solo recibe texto y devuelve texto.
- **Costo del modelo:** el análisis envía al modelo como máximo 30 000 caracteres por app (S12).
- **Rendimiento:** el análisis de un sitio tiene un tiempo máximo de 120 segundos; pasado ese tiempo responde 502 y no deja la app a medias.
- **Abuso y costo:** se limita la creación de apps a 5 por hora por cuenta y el simulador a 30 mensajes por hora por cuenta (S13), aplicado en FastAPI.
- **Sesión:** la cookie de sesión es `HttpOnly` y `SameSite=Lax`, y `Secure` cuando haya HTTPS. El flujo OAuth genera y valida el parámetro `state` (S14).
- **Privacidad:** de la cuenta solo se guarda el proveedor, el identificador y el nombre. El texto del sitio se envía al proveedor del modelo de lenguaje (Q1). Las llamadas del panel no guardan contenido.
- **Exposición por el túnel:** solo el puerto del servidor MCP. La interfaz web y la API de generación no se exponen.
- **Alcance de la demo:** es una demostración, sin garantías de disponibilidad. Un túnel de pruebas sirve para conectar en ChatGPT, pero la propia guía de OpenAI aclara que no sustituye el punto de conexión HTTPS público que exige el envío al directorio.

### 6.6 Estrategia de pruebas

- Runner: `pytest`. Comando: `pytest`.
- Un sitio de ejemplo estático, servido localmente como fixture, y un modelo de lenguaje simulado con respuestas fijas.
- La calidad real de la metadata y de las respuestas del simulador se revisa a mano en la demo; no es una prueba automática.
- TDD: el equipo no lo declaró. No se exige.

Casos de prueba:

| # | Entrada | Resultado esperado |
|---|---|---|
| C1 | URL del sitio de ejemplo | 200; app con nombre, descripción y al menos una herramienta |
| C2 | URL sin esquema `http` o `https` | 422; no se crea la app |
| C3 | URL de un dominio que no responde | 502; no se crea la app |
| C4 | URL que resuelve a una dirección privada | 422; no se hace la petición |
| C5 | Sitio cuyo `robots.txt` prohíbe el acceso | 422 con el motivo; no se crea la app |
| C6 | Sitio con más de 20 páginas | La app se crea con exactamente 20 páginas de contenido |
| C7 | Despliegue sin verificación | 403 |
| C8 | Verificación con la etiqueta presente | La app queda verificada |
| C9 | Verificación sin la etiqueta | 409 |
| C10 | Despliegue de una app verificada | 200; la URL MCP responde la lista de herramientas, igual a la del simulador |
| C11 | Llamada a una herramienta de la app desplegada | El panel suma una llamada a esa herramienta |
| C12 | Llamada a una herramienta con error | El panel suma un error y no guarda el texto de la consulta |
| C13 | Mensaje al simulador sobre un dato del sitio | La respuesta indica la herramienta invocada |
| C14 | Paquete de una app verificada | Incluye los campos de 6.10, exactamente cinco casos positivos con `tools_triggered` y `expected_behavior` (cada herramienta nombrada existe en la app) y tres negativos, los textos de privacidad y términos, y la guía |
| C15 | Nombre de la app de más de 30 caracteres | El paquete lo acorta a 30 caracteres o menos |
| C16 | Petición al servidor MCP por la ruta `/apps/{id}/mcp` | Responde con transporte HTTP en streaming y la lista de herramientas. Se automatiza en `pytest` con el cliente de pruebas de FastAPI (`TestClient`, basado en `httpx`) montando el servidor MCP como aplicación ASGI; MCP Inspector queda como comprobación manual. Si `TestClient` no soporta el transporte en streaming, se usa el cliente MCP del SDK de Python contra el servidor levantado dentro de la prueba (S16) |
| C17 | Cualquier endpoint `/api/*` sin sesión | 401 |
| C18 | Una cuenta pide una app que es de otra | 404; no se revela que existe |
| C19 | Inicio de sesión con un proveedor no admitido | 404 |
| C20 | Cuenta con 5 apps creadas en la última hora que crea otra | 429 |
| C21 | App desplegada que el dueño retira | La lista de herramientas MCP de esa app responde 404 |
| C22 | `POST /api/apps` | La respuesta incluye `token_verificacion`; la verificación con un token de otra app falla con 409 |
| C23 | Herramienta `buscar` con una consulta sin coincidencias | Lista vacía, sin error |
| C24 | Cuenta que envía el mensaje 31 al simulador en una hora | 429 |
| C25 | Paquete con una descripción corta de más de 30 caracteres | La descripción corta del paquete tiene 30 caracteres o menos |
| C26 | Retorno de OAuth con un `state` distinto del emitido | Se rechaza el inicio de sesión; no se crea sesión |

Pruebas de interfaz: con una URL inválida, el formulario muestra el error junto al campo y no envía la petición.

### 6.7 Diseño de la interfaz

Cuatro vistas: formulario de URL, simulador con chat, paquete de publicación y panel. Sin sistema visual propio en esta rebanada.

### 6.8 Supuestos (aprobados)

- S1: las herramientas son tres, de solo lectura, y las genera el sistema sin edición manual.
- S2: servir todas las apps desde un solo servidor MCP, en un puerto aparte del de la interfaz, es suficiente para la demo.
- S3: la verificación de propiedad se hace con una etiqueta `<meta name="mcp-gemela" content="TOKEN">` en la página de inicio o un archivo `/.well-known/mcp-gemela.txt` con el token.
- S4: el simulador es una aproximación; la prueba real se hace en el modo de desarrollador de ChatGPT.
- S5: el paquete cubre los campos y los casos de prueba que exige la [guía oficial de envío](https://developers.openai.com/apps-sdk/deploy/submission). El dueño completa lo que el sistema no puede generar (6.10).
- S7: el token de verificación lo entrega `POST /api/apps` y la comprobación busca ese token (6.3).
- S8: los criterios 2 y 3 se prueban con una app verificada; la verificación es opcional solo para generar y probar en el simulador.
- S9: las tres herramientas se definen en 6.2.
- S10: la prueba C16 se automatiza en `pytest` con el cliente de pruebas de FastAPI; MCP Inspector queda como comprobación manual.
- S11: el dueño puede retirar una app (`POST /api/apps/{id}/retiro`).
- S12: el análisis envía al modelo como máximo 30 000 caracteres por app. Valor inicial, ajustable.
- S13: el simulador admite hasta 30 mensajes por hora por cuenta; el siguiente responde 429.
- S14: la cookie de sesión es `HttpOnly` y `SameSite=Lax` (y `Secure` con HTTPS); el flujo OAuth usa y valida `state`.
- S15: el criterio 1 nombra las tres herramientas y el paso 5 aclara que el despliegue requiere verificación.
- S16: si `TestClient` no soporta el streaming de MCP, C16 usa el cliente MCP del SDK de Python; `shortDescription` se acorta a 30 caracteres.
- S6: la interfaz admite Google y GitHub; basta con que funcione uno para la demo, y el otro se añade con la misma estructura. La cuenta es la identidad del dueño en el panel.

### 6.9 Decisiones resueltas y preguntas abiertas

- Q1 (resuelta): OpenAI, el modelo más económico disponible, configurable por `MODELO_LLM`. Riesgo asumido: un modelo barato puede dar metadata y respuestas más flojas; se mitiga limitando el texto que se le envía y revisando la calidad a mano en la demo.
- Q2 (resuelta): túnel de ngrok con dominio estático gratuito, solo sobre el puerto del servidor MCP. Según [ngrok](https://ngrok.com/compare/cloudflare-tunnel), el plan gratuito incluye un dominio estático, así que la URL no cambia entre reinicios, a diferencia del túnel rápido de Cloudflare, cuya URL aleatoria se pierde al detenerlo. Es dato del propio proveedor; verificar los límites vigentes en su página de precios al crear la cuenta. La guía de OpenAI menciona además un «Secure MCP Tunnel» propio; no se evaluó su costo.
- Q3 (resuelta): el estándar es un servidor MCP con transporte HTTP en streaming en una ruta `/mcp`. La página de anuncio de OpenAI no se pudo leer (error 403), así que esto se apoya en la documentación para desarrolladores. Esta rebanada no usa interfaz propia dentro de ChatGPT: solo herramientas. En la documentación de OpenAI el producto aparece como «Plugins».
- Q4 (resuelta): el envío al directorio se hace solo desde el panel de OpenAI, con la carga de un archivo ZIP; no hay API de envío. Detalles en 6.10.
- Q5 (resuelta): el dueño se autentica con Google o GitHub (6.1). El panel y el resto de acciones son solo de la cuenta dueña de la app (BR-MCP-07). Pendiente al implementar: registrar la aplicación en cada proveedor para obtener las credenciales OAuth, con la URL de retorno local.
- Q6 (resuelta): estructura del ZIP según la guía oficial de envío, con la disposición Agent Plugins. Ver [ADR 0003](decisions/0003-formato-zip-envio.md) y la sección 6.10. Quedan tres puntos que la guía no cubre y que se confirman al subir el primer paquete real.

### 6.10 Paquete de publicación

Datos verificados en la [guía oficial de envío](https://developers.openai.com/apps-sdk/deploy/submission):

- Envío solo desde el panel, con un archivo ZIP. Lo hace el propietario de la organización de OpenAI, o un miembro con el rol «Apps Management Write», y la organización debe tener verificación de individuo o de empresa.
- Campos de listado: `displayName` (máximo 30 caracteres), `shortDescription` (máximo 30), `longDescription` (máximo 4000), `developerName` y `category`.
- Cuatro URL, todas HTTPS y públicas, que deben identificar al mismo editor que el envío: sitio web, soporte, política de privacidad (máximo 1024 caracteres) y términos de servicio.
- Iconos cuadrados de al menos 48×48 píxeles, en PNG, JPEG, WebP o SVG, de hasta 5 MiB.
- Exactamente cinco casos de prueba positivos (con `tools_triggered` y `expected_behavior`) y tres negativos.
- URL de un video de demostración accesible para los revisores.
- Sin cuenta de prueba: el portal admite apps sin autenticación, y la app generada no la requiere.

Qué genera el sistema y qué completa el dueño:

| Lo genera el sistema | Lo completa el dueño |
|---|---|
| Nombre, descripciones y categoría sugeridos, dentro de los límites | `developerName` y la verificación de su organización en OpenAI |
| Los ocho casos de prueba | El video de demostración |
| Textos de política de privacidad y de términos | Publicarlos en una URL HTTPS de su propio sitio, y aportar las URL de sitio web y soporte |
| URL del servidor MCP | Un punto de conexión HTTPS permanente: el túnel de la demo no basta para el envío |
| Guía paso a paso, con el aviso de que el simulador es una aproximación y de que el plan de ChatGPT debe permitir servidores MCP personalizados | Iconos |

### Estructura del ZIP

El ZIP usa la disposición Agent Plugins: `plugin.json`, `mcp.json`, una carpeta `skills/` con una skill de bienvenida y una carpeta `assets/` con los iconos. El detalle, las restricciones y lo que la guía no cubre están en el [ADR 0003](decisions/0003-formato-zip-envio.md).
