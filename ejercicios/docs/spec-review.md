# Revisión de spec: app MCP gemela de un sitio web para ChatGPT

Evaluada con `ejercicios/skills/evaluate-spec/SKILL.md`. Segunda revisión de esta spec.
Spec evaluada: `ejercicios/docs/spec-mcp-gemela.md`.
Historial: B en la primera revisión, con tres vacíos (verificación incompleta, herramientas sin definir, sin retiro de apps). Los supuestos S7 a S12 los cerraron.

## 1. Notas por ola

| Ola | Nota | Justificación |
|---|---|---|
| Rebanada 1: pegar URL, simular, desplegar y medir (demo) | **A** | Todos los críticos cumplen. Quedan huecos no críticos (costo del simulador, endurecimiento de la sesión, formato del ZIP) con acción propuesta. |

## 2. Recomendación

Planificar esta ola ya. Dos condiciones para el plan: la primera tarea del paso 6 debe ser investigar el formato del ZIP de envío (Q6), y los supuestos S13 a S16 (sección 6) deben entrar como tareas, no quedarse como notas. Antes de instalar nada con costo, confirmar los límites vigentes del plan gratuito de ngrok (Q2).

## 3. Evaluación por lente

Artefactos revisados: la spec y el estado del repo. No existen `AGENTS.md`, `design.md`, código ni pruebas, lo cual es esperable antes de implementar.

### Producto

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| P1 (*) Problema y usuario | Cumple | Secciones 1 y 2 | Ninguna. |
| P2 (*) Alcance | Cumple | Sección 3, siete pasos | El paso 5 debería decir que el despliegue exige verificación (S15). |
| P3 (*) Fuera de alcance | Cumple | Sección 5 | Ninguna. |
| P4 (*) Reglas de negocio | Cumple | 6.4, BR-MCP-01 a 09, sin contradicciones | Ninguna. |
| P5 Criterio de éxito | Cumple | Sección 1, «Éxito de la rebanada» | Cualitativo; medirlo en la demo. |
| P6 Decisiones pendientes | Cumple | 6.9, con Q6 como tarea de investigación | Ninguna. |

### TDD

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| T1 (*) Aceptación observable | Cumple | Sección 4; el criterio 2 ya exige verificación | El criterio 1 dice «al menos una herramienta» pero la spec define tres fijas (S15). |
| T2 (*) Casos de prueba | Cumple | 6.6, C1 a C23 con entrada y resultado, más prueba de interfaz | Añadir un caso para el límite de 30 caracteres de `shortDescription` (S16). |
| T3 Runner y comando | Cumple | 6.6, `pytest` | Ninguna. |
| T4 Declaración TDD | N/A | El equipo no la declaró | No imponerla. |

### Diseño

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| D1 (*) Arquitectura | Cumple | 6.2: componentes, tabla de herramientas, modelo de datos, servidor MCP separado del túnel | Ninguna. |
| D2 Contratos | Parcial | 6.3 define los endpoints. El formato del ZIP de envío no está definido (Q6) | Tarea de investigación ya prevista. |
| D3 design.md | Parcial | 6.7 nombra cuatro vistas; no hay `design.md` | Suficiente para una demo. |
| D4 Restricciones | Parcial | 6.5 cubre lectura de URLs, rendimiento, privacidad y exposición. Faltan un tope de uso del simulador y los datos de seguridad de la sesión | S13 y S14. |

## 4. Hallazgos de coherencia entre artefactos

1. **El simulador no tiene tope de costo.** Cada mensaje llama al modelo de lenguaje, y el único límite de la spec es el de creación de apps. Una cuenta puede generar gasto ilimitado.
2. **La sesión y OAuth no tienen detalles de seguridad escritos:** parámetro `state` del flujo OAuth, atributos de la cookie y protección de las peticiones POST.
3. **Punto público sin límite:** la ruta MCP de una app desplegada es pública (BR-MCP-08) y lee de la base de datos. Para una demo basta con los límites del túnel; conviene saberlo antes de compartir la URL.
4. **Análisis síncrono de hasta 120 segundos:** `POST /api/apps` es una sola petición. En local funciona; con un proxy intermedio podría cortarse. No se pide cambiarlo, pero hay que conocerlo si se despliega fuera de la demo.
5. **Verificar, `TestClient` y MCP en streaming:** la spec decide probar C16 con el cliente de pruebas de FastAPI. No se comprobó que maneje el transporte en streaming de MCP. Falta escribir la alternativa (S16).
6. **Verificar, ngrok:** que el plan gratuito incluya un dominio estático es afirmación del proveedor (Q2).
7. **Verificar, ChatGPT:** que el plan de ChatGPT del dueño permita servidores MCP personalizados no está comprobado; la guía del paquete lo avisa.
8. **Estado del repo:** el `README.md` no describe el proyecto y no hay `AGENTS.md`. `create-implementation-plan` los generará.

## 5. Los tres vacíos más graves

Ninguno es crítico. Por impacto:

1. **Costo sin tope en el simulador (hallazgo 1).** Es el único punto donde un usuario puede producir gasto ilimitado.
2. **Formato del ZIP desconocido (Q6).** Si es complejo, el paso 6 puede crecer más de lo esperado.
3. **Seguridad de sesión sin escribir (hallazgo 2).** Es barata de cerrar ahora y cara de olvidar.

## 6. Supuestos propuestos

Todos aprobados e incorporados a la spec (S1 a S16).

| # | Supuesto | Cierra |
|---|---|---|
| S13 | El simulador admite hasta 30 mensajes por hora por cuenta; el siguiente responde 429. Nuevo caso de prueba. | D4, hallazgo 1 |
| S14 | La cookie de sesión es `HttpOnly` y `SameSite=Lax` (y `Secure` cuando haya HTTPS); el flujo OAuth usa y valida el parámetro `state`. | D4, hallazgo 2 |
| S15 | El criterio 1 pasa a decir «las tres herramientas, con descripciones generadas a partir del contenido del sitio», y el paso 5 del flujo aclara que el despliegue requiere verificación. | T1, P2 |
| S16 | Si `TestClient` no soporta el transporte en streaming de MCP, C16 se prueba con el cliente MCP del SDK de Python contra el servidor levantado dentro de la prueba. Nuevo caso: `shortDescription` de más de 30 caracteres se acorta. | T2, hallazgo 5 |

## 7. Qué hacer ahora

S13 a S16 ya están en la spec. Pasar a `create-implementation-plan`. La spec ya no necesita más rondas de evaluación.
