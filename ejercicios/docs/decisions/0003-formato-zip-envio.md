# ADR 0003: formato del ZIP de envío a ChatGPT

- Estado: aceptada.
- Fecha: 2026-11-03.
- Fuente: [guía oficial de envío de OpenAI](https://developers.openai.com/apps-sdk/deploy/submission), leída el 2026-11-03.

## Contexto

El envío al directorio se hace desde el panel de OpenAI subiendo un ZIP. La spec dejó abierta (Q6) la estructura exacta. La guía describe dos disposiciones, y hay que usar solo una.

## Decisión

Generar el ZIP con la disposición **Agent Plugins**, que la guía presenta como el formato portable, y no con la disposición Codex, que llama «manifiesto de compatibilidad». Que el formato Codex sea el exigido para ChatGPT no lo dice la guía, y no se asume.

```text
<nombre>.zip
├── plugin.json        manifiesto; ajustes de OpenAI bajo extensions.com.openai
├── mcp.json           configuración MCP, clave "mcpServers"
├── skills/
│   └── <skill>/SKILL.md   skill de bienvenida, con name y description en la cabecera YAML
└── assets/
    ├── icon.png, icon-dark.png
    ├── logo.png, logo-dark.png
    └── screenshot.png
```

Campos del manifiesto que la guía exige:

- `name`: identificador estable, hasta 64 caracteres, minúsculas, números y guiones simples.
- Bajo `extensions.com.openai.interface`: `displayName`, `shortDescription`, `longDescription`, `developerName` y `category`.
- Para revisión MCP: `websiteURL`, `supportURL`, `privacyPolicyURL` y `termsOfServiceURL`, todas HTTPS.
- En `mcp.json`, bajo `mcpServers.<nombre>`: `"type": "streamable-http"` y `"url"`.
- Rutas de iconos con prefijo `./` y relativas a la raíz del plugin; los archivos referenciados deben estar incluidos.

## Restricciones que la guía impone

- Solo se admite **un** servidor MCP por plugin.
- La URL del servidor debe ser un punto HTTPS público y estable. El túnel de la demo no basta para el envío.
- El envío público rechaza `headers` no vacíos en el servidor. No se ponen tokens ahí.
- El ZIP no puede llevar `test_credentials` ni `reviewer_instructions`; el acceso de los revisores se escribe en el panel.
- No se admiten referencias a apps (`apps`, `.app.json`) ni ganchos de ciclo de vida.
- Iconos y logos cuadrados, de al menos 48×48 px, de hasta 5 MiB y 4096 px por lado, en PNG, JPEG, WebP o SVG.

## Lo que la guía no cubre

- La estructura de carpeta raíz exacta dentro del ZIP.
- El contenido de `SKILL.md` más allá de `name` y `description`.
- Los mensajes de error de validación y cómo corregirlos.

Esos tres puntos se resuelven al generar el primer paquete real y subirlo al panel; la tarea del paquete debe registrar lo que se aprenda.

## Consecuencias

- El generador del paquete produce `plugin.json`, `mcp.json`, una skill de bienvenida y la carpeta `assets/`.
- Los iconos los aporta el dueño; el paquete incluye marcadores y la guía lo avisa.
- El sistema no puede cumplir por sí solo el requisito de URL estable y pública.
