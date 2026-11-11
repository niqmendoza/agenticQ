# Generación con Qwen 4B y contexto verificable

29/10/2026. **La integración local entregó cinco borradores y una abstención por información faltante. QA todavía debe revisarlos.** No se ejecutó la aplicación ni se publicaron casos en Azure.

## Qué se implementó

`scripts/draft_cases.py` recibe un paquete `qa-context/1`, comprueba su integridad y construye un catálogo legible con IDs cortos. El 4B selecciona reglas y clasifica si hay respaldo o falta información. Después propone pasos funcionales y elige qué regla respalda el esperado.

El script copia la regla y resuelve las referencias desde el catálogo, conservando el texto crudo y sus posiciones dentro del fragmento. Esto impide que el modelo escriba libremente otro esperado o invente una cita textual aceptada por esta interfaz. **No prueba que eligió la regla adecuada ni que los pasos realmente la comprueben.** El esperado documental puede requerir reformulación como comprobación observable por QA.

## Ensayo integrado

Se usó RAGFlow en vivo mediante el CLI de recuperación y después el CLI del generador, con `qwen3.5:4b` en Ollama. El protocolo pidió dos fragmentos por consulta y fijó cuatro consignas antes de la primera ejecución: tres regresiones del ensayo anterior y una sobre idiomas que era nueva para el generador al comenzar estas iteraciones.

| Consigna | Estado final | Borradores | Llamadas al modelo | Entrada nativa | Salida nativa |
|---|---|---:|---:|---:|---:|
| roles | draft_for_qa | 2 | 2 | 1612 | 506 |
| url-contraejemplo | draft_for_qa | 1 | 2 | 1947 | 345 |
| regla-ausente | needs_information | 0 | 1 | 1097 | 125 |
| idioma-nuevo | draft_for_qa | 2 | 2 | 1857 | 658 |

La última ejecución sumó **7 llamadas**, **6.513 tokens nativos de entrada** y **1.634 de salida**. Son conteos de Ollama, sin Copilot. Separar etapas añade llamadas; no se presenta este ensayo como una medición de ahorro frente a un flujo de calidad equivalente.

Se cotejaron todos los esperados y referencias de los cinco borradores contra el catálogo reconstruido y los recortes originales. La suite ampliada pasó **57 tests**, incluidos límites, errores HTTP, respuestas cortadas, abstención, fuentes alteradas, cantidades y campos de aprobación no permitidos.

## Mejoras y pendientes observados

- **Roles:** el borrador negativo conserva que `pending` sólo puede ver espera. La transición incluye el cambio por admin, pero todavía falta un intento posterior de acceso al chat.
- **URLs:** la propuesta respeta que una URL ya emitida sigue válida hasta expirar y la usa después del cambio de permisos. La sugerencia equivocada queda señalada; no se inventó un código HTTP en el esperado.
- **Información ausente:** no se creó un caso para los quince minutos no documentados. El flujo se detuvo después de la selección, con una pregunta abierta.
- **Idiomas:** reconoce es-AR y que en-US se retiró. Un esperado principal quedó demasiado general; las referencias de apoyo sí incluyen la regla concreta y QA debe precisar la comprobación.

[Primer lote completo para revisar](PARA-REVISION-QA-4B.md), con estos pendientes visibles antes de cada borrador.

## Iteraciones conservadas

La primera versión frenó las cuatro tareas: interpretó intentos de acciones prohibidas y falta de detalles técnicos como ausencia de reglas. La segunda produjo los dos borradores de idiomas y siguió frenando los otros casos respaldados. La tercera distingue la evaluación de fuentes de la construcción de pasos a alto nivel y produjo el lote descrito.

Las tres carpetas `results/2026-10-29-grounded-v1`, `-v2` y `-v3` conservan solicitudes, respuestas, contextos y resúmenes. Las dos primeras incluyen el prototipo anterior a cada ajuste. La tercera conserva el código de cierre, con el verificador añadido después de las generaciones; sus trazas conservan las solicitudes y respuestas exactas de la ejecución. Los Markdown de v3 se volvieron a renderizar desde el mismo JSON para mostrar también las reglas de apoyo; se conserva la primera representación como `PARA-REVISION-QA.original.md`.

Estos ajustes usaron los resultados anteriores como retroalimentación: **no es una evaluación ciega ni una prueba general de calidad**. Una muestra por tarea en la versión final no demuestra estabilidad. Las consignas se diseñaron para este ensayo; falta una tarea real con documentación funcional aprobada y revisión del equipo de QA.

## Qué sigue

Revisar el lote con QA y registrar correcciones, descartes y faltantes. A continuación usar una funcionalidad real del piloto, comprobar vigencia del conocimiento y comparar con los casos existentes antes de pensar en publicar. Desarrollo permanece informado, sin autorización obligatoria sobre los casos.

[Guía de uso](../GUIA-GENERACION-4B.md). Las integraciones con Azure, n8n y Playwright permanecen pendientes. El contrato de borradores es experimental y no reemplaza el formato de Test Plans.
