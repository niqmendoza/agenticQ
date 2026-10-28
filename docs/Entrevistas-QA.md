# Reuniones para aprender con QA

**Guía propuesta · 5 de octubre de 2026.** No hay reuniones registradas todavía. La secuencia se adapta a la disponibilidad del equipo; no presupone respuestas ni requiere entrevistar a todos de una vez.

Volver a la [guía principal](Guia-relevamiento-QA.md) · Usar la [plantilla de reunión](plantillas/Reunion-QA.md).

## Primera reunión: diez preguntas esenciales

Objetivo: observar un caso manual y una corrida automática, siguiendo su resultado hasta donde se pueda. Podés abrir así: “Quiero aprender como trainee. Mostrame un ejemplo real mientras anotamos los pasos; donde no entienda algo, lo dejamos como pregunta”. Pedí permiso al equipo antes de grabar y acordá dónde conservar la transcripción. Si no hay grabación, tomá notas con referencias.

| Pregunta para hacer | Por qué hacerla | Qué pedir ver o registrar |
| --- | --- | --- |
| 1. ¿Qué hace que hoy prueben algo y cómo eligen los casos? | Entender el disparador y la prioridad antes de generar más casos. | Cambio, ticket o solicitud; criterio de riesgo y selección. |
| 2. ¿Me mostrás dónde está ese caso en Azure y si lo usan en otros planes o suites? | Reutilizarlo y evitar cambios que afecten otros usos sin saberlo. | Plan, suite, ID, vínculos y relaciones compartidas. |
| 3. ¿Podés hacer una prueba manual de API mientras te sigo? ¿Qué preparás antes de entrar a Swagger? | Descubrir pasos y decisiones que no aparecen en el caso escrito. | Ambiente, operación, datos, acceso por referencia, request depurado y pasos reales. |
| 4. ¿Cómo sabés qué resultado debería dar? ¿Quién resuelve una duda funcional? | Evitar convertir el comportamiento actual en una regla incorrecta. | Esperado, fuente funcional o persona de referencia; contradicciones. |
| 5. ¿Me mostrás una corrida automática reciente y qué la disparó? | Integrar lo que ya funciona y localizar su ejecución real. | Hora, ID, enlace, disparador, configuración y quién la mantiene. |
| 6. ¿Dónde ves que pasó o falló y cómo volvés desde ese resultado al caso? | Comprobar trazabilidad y distinguir publicación de asociación. | Resultado concreto, publicación y vínculo visible o faltante. |
| 7. ¿Cómo consiguen datos y un ambiente adecuado? ¿Qué limpian después? | Entender qué hace reproducible una prueba y qué provoca esperas o fallos. | Preparación, dependencias, versiones, limpieza y responsables; sin secretos. |
| 8. ¿Qué hacen con un caso viejo, duplicado o con un esperado dudoso? | Preservar historia y aprender el criterio para revisar legacy. | Ejemplo con ID, decisión y evidencia; si falta, queda pendiente. |
| 9. Cuando falla, ¿quién decide qué ocurrió y cómo llega a desarrollo y vuelve a QA? | Seguir el ciclo completo hasta verificar la corrección. | Informe/defecto, evidencia, corrección, reejecución y cierre. |
| 10. ¿Dónde pierden más tiempo o repiten trabajo? ¿Qué parte necesita juicio humano? | Elegir un problema valioso para el piloto y conservar la revisión necesaria. | Situación concreta, frecuencia y consecuencia; medición o percepción. |

No es un examen de herramientas. Si no saben quién administra el runner, anotá quién podría mostrarlo en otra reunión. Si una respuesta parece general, pedí “¿podemos verlo en este caso?”. Si no se ve el cierre en vivo, usen un defecto ya cerrado como evidencia histórica, indicando su fecha.

Durante la sesión observá búsquedas, esperas, decisiones y excepciones, además de los clics o requests. En la primera semana devolvé el mapa a QA para contrastarlo y conversá con negocio/producto sobre quién define lo correcto. La meta es validar ambos recorridos, asignar responsables a preguntas abiertas y elegir un problema prioritario; no diseñar todavía toda la arquitectura.

**Salida esperada:** nota con fuentes, borrador del recorrido manual, borrador del automático y principales dudas. No se da por validado todo el mapa porque una sola prueba funcionó.

## Segunda reunión: automatizaciones y trazabilidad

Participación propuesta: QA y alguien que mantenga las automatizaciones o la ejecución. Objetivo: completar las partes desconocidas del recorrido automático existente.

| Preguntas posteriores | Evidencia útil |
| --- | --- |
| ¿En qué repositorio y archivos está la prueba del ejemplo? ¿Qué framework y versiones usan? | Enlace, archivo, identificador de test, revisión y configuración. No asumir Azure Repos. |
| ¿Qué comando/runner la ejecuta y en qué máquina, agente o servicio? | Comando real, configuración depurada, entorno de ejecución y responsable. |
| ¿Se dispara por cambio, despliegue, horario o acción manual? ¿Cómo selecciona un subconjunto? | Pipeline o configuración equivalente, filtros/tags, variables y una corrida vinculada. |
| ¿Cómo parametrizan los datos automáticos? ¿Coinciden con las iteraciones manuales? | Ejemplo en código/configuración y correspondencia documentada. No asumir transferencia automática. |
| ¿Qué publica el resultado y qué crea la asociación con el caso en Test Plans? | Tarea/adaptador/formato, identidad del test y vínculo comprobable desde Azure. Registrar ambos pasos. |
| ¿Cómo guardan evidencia y cuánto tiempo permanece accesible? | Logs, respuestas, capturas o trazas; enlaces, retención y acceso de QA/desarrollo. |
| ¿Qué licencias, permisos y versión de Azure usan para estas operaciones? | Azure DevOps Services o Server y versión; matriz de acceso existente o revisión con su responsable. |
| ¿Qué hacen con fallos intermitentes, reintentos y pruebas omitidas? | Historial de resultados, motivo de exclusión y quién revisa/mantiene la prueba. |

Azure diferencia permisos y niveles de acceso según la operación; verificarlos para las personas e integraciones del piloto, sin presuponer acceso completo. [Requisitos de Azure Test Plans](https://learn.microsoft.com/en-us/azure/devops/test/automated-testing-overview?view=azure-devops).

**Salida esperada:** ficha automática corregida, cadena caso → código → corrida → resultado/evidencia, vacíos visibles y responsable de mantenimiento por definir o identificado.

## Tercera reunión: negocio, legacy y conocimiento

Participación propuesta: QA y alguien que conozca el negocio del flujo. Objetivo: distinguir comportamiento observado de regla esperada y revisar cobertura existente.

| Preguntas posteriores | Evidencia útil |
| --- | --- |
| ¿Qué objetivo tiene el flujo y cuáles son sus reglas, límites y excepciones críticas? | Regla escrita o confirmación atribuida con alcance; ejemplos válidos y no válidos. |
| ¿Qué hacemos si código, notas, OpenAPI y caso legacy se contradicen? | Conflicto concreto, persona que decide, resolución y versión aplicable. |
| ¿Qué casos se conservan, actualizan, retiran o duplican a propósito? ¿Quién aprueba? | Inventario pequeño con IDs, vigencia, modo de ejecución y usos compartidos. |
| ¿Cómo se enteran de cambios y mantienen casos, datos, pruebas y notas? | Cambio reciente con su recorrido y esfuerzo de mantenimiento. |
| ¿Podemos ver el workbook y unas notas de Obsidian usadas para generar casos? | Versión del workbook, instrucciones/MCP realmente disponibles, fuentes de notas y validaciones. Sigue pendiente hasta verlo. |
| ¿Qué puede proponer IA y qué decisiones deben seguir revisando ustedes? | Criterios de revisión funcional, cobertura, exploración y aceptación de hallazgos. |

**Salida esperada:** primeras reglas con fuente y estado, clasificación de una muestra legacy y dudas funcionales priorizadas. La transcripción no convierte en validado un resumen que el conocedor no revisó.

## Cuarta reunión: validar el mapa y elegir un piloto

Mostrá las fichas y diagramas al equipo. Preguntá qué falta, qué excepción cambia el recorrido y qué partes solo describen una aplicación. Revisen un piloto de alcance pequeño y medible; su ejecución vendrá después del relevamiento.

- ¿Qué flujo tiene valor, datos reproducibles y alguien disponible para validar negocio?
- ¿Qué casos legacy sirven y qué faltante justifica un caso nuevo?
- ¿Qué evidencia demostrará ejecución, publicación y asociación reales?
- ¿Quién revisa propuestas, código, hallazgos y cierre? ¿Cómo se informa cada cambio?
- ¿Qué tiempos/esfuerzo actuales podemos medir para comparar revisión, reproducción y mantenimiento?
- ¿Qué dependencia o permiso falta y cuál es la próxima acción concreta?

**Salida esperada:** mapa confirmado dentro de su alcance, preguntas pendientes y piloto propuesto o confirmado en el [registro](Registro-QA.md). Elegir la vía de integración depende de estas respuestas; n8n e IBM siguen siendo opciones futuras.
