# Spec mínima de una rebanada

Una página. Describe **un solo flujo** de tu producto que un usuario pueda completar de punta a punta. Es lo que vas a implementar, probar, desplegar y mostrar en el Demo Day.

Si ya tienes PRD, Inception o Construction, enlázalos y toma de ahí lo que necesites. Si no, esta página alcanza para empezar.

## 1. Problema

Una o dos frases: qué le duele a quién.

> Ejemplo: Los reclutadores de BPO pierden días coordinando primeras entrevistas que podrían filtrarse con un chat.

## 2. Usuario

Quién usa este flujo. Uno solo.

> Ejemplo: El reclutador que abre una vacante nueva.

## 3. El flujo, paso a paso

De 3 a 7 pasos, desde que el usuario empieza hasta que obtiene el resultado.

> Ejemplo:
> 1. El reclutador entra al dashboard.
> 2. Crea una campaña con nombre del cargo y tres preguntas.
> 3. Guarda la campaña.
> 4. El sistema le muestra un link para compartir con candidatos.

## 4. Criterios de aceptación

Exactamente tres. Cada uno tiene que poder comprobarse con un test.

> Ejemplo:
> - [ ] Al guardar una campaña válida, aparece en la lista con estado «Activa».
> - [ ] Si falta el nombre del cargo, el formulario muestra un error y no guarda.
> - [ ] El link generado abre una página con el nombre del cargo.

## 5. Qué queda fuera

Todo lo que **no** entra en esta rebanada. Es la sección que más protege tu tiempo.

> Ejemplo: autenticación, edición de campañas, el bot de Telegram, la evaluación de candidatos.

## 6. Decisiones técnicas

Solo las que ya están tomadas: lenguaje, framework, base de datos y dónde se despliega. Si algo no está decidido, escríbelo como pregunta.

> Ejemplo: Next.js y PostgreSQL. Despliegue: por decidir en E9.

---

Cuando la tengas, evalúala con la skill [`evaluate-spec`](../skills/evaluate-spec/SKILL.md) y corrige hasta nota A o B.