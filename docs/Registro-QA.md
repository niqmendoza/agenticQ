# Registro de decisiones, preguntas y próxima acción

**Inicio: 5 de octubre de 2026.** Documento editable. No contiene respuestas de QA ni reuniones inventadas. “Confirmada por usuario” registra un requisito expresado; no significa implementación comprobada. Los responsables operativos siguen por definir.

Volver a la [guía](Guia-relevamiento-QA.md) · Consultar [entrevistas](Entrevistas-QA.md).

## Decisiones y propuestas

| ID | Decisión o propuesta | Estado | Responsable | Evidencia y alcance | Próxima acción |
| --- | --- | --- | --- | --- | --- |
| D-01 | Mantener Azure Test Plans e integrar casos legacy sin reemplazo o duplicación indiscriminados. | Confirmada por usuario | Por definir | Pedido del usuario, 05/10/2026; requisito de diseño. | Ver inventario y usos compartidos del flujo observado. |
| D-02 | Aprender con QA y conservar reuniones, fichas y decisiones en Markdown. | Confirmada por usuario | Por definir | Pedido del usuario, 05/10/2026; documentación autorizada. | Observar un caso manual y una corrida automática. |
| D-03 | Validar documentación funcional con un conocedor antes de aceptar esperados de negocio. | Propuesta | Por definir | Contexto aportado por usuario; guía, circuito objetivo. No hay validaciones realizadas. | Identificar conocedor y revisar una regla concreta. |
| D-04 | Copilot como interfaz inicial; código versionado ejecutado por runner/pipeline y trazado a Azure. | Propuesta | Por definir | Recomendación preliminar; infraestructura actual desconocida. | Relevar automatización y publicación existentes. |
| D-05 | Hacer piloto pequeño con legacy y casos nuevos justificados antes de escalar. | Propuesta | Por definir | Guía, criterios de piloto. Aplicación todavía no elegida. | Validar mapa y seleccionar flujo con QA. |
| D-06 | Evaluar MCP oficial, API u otra vía sin imponer MCP; considerar n8n/IBM más adelante. | Propuesta | Por definir | Contexto del usuario; producto IBM sin definir. Sin instalación autorizada. | Conocer necesidades y compatibilidad del piloto antes de elegir. |

## Preguntas abiertas priorizadas

| ID | Prioridad y pregunta | Estado | Responsable | Evidencia actual o faltante | Próxima acción |
| --- | --- | --- | --- | --- | --- |
| P-01 | Primero: ¿cómo eligen pruebas y qué inicia el trabajo? | Abierta | Por definir | Falta recorrido real con QA. | Observar selección de un caso. |
| P-02 | Primero: ¿dónde corren automatizaciones, con qué framework/runner y disparador? | Abierta | Por definir | Se sabe por relato que existen y corren automáticamente; faltan repositorio, comando y configuración. | Ver corrida reciente y quién la mantiene. |
| P-03 | Primero: ¿cómo se publican resultados y se asocian con casos/requisitos? | Abierta | Por definir | Falta evidencia del vínculo en Azure. | Seguir resultado → caso y registrar ambos mecanismos. |
| P-04 | Primero: ¿quién confirma esperados y resuelve contradicciones funcionales? | Abierta | Por definir | Código/notas no bastan; no hay regla validada en estos documentos. | Pedir fuente de un esperado y conocedor del flujo. |
| P-05 | Primero: ¿cómo preparan datos, ambiente, versiones, accesos y limpieza? | Abierta | Por definir | Falta configuración observada. | Ver preparación de prueba manual/automática sin secretos. |
| P-06 | Primero: ¿cómo clasifican un fallo, lo reportan, corrigen y cierran? | Abierta | Por definir | Falta defecto con historia y reejecución. | Recorrer ejemplo con QA. |
| P-07 | Después: ¿qué legacy sigue vigente y qué referencias están compartidas? | Abierta | Por definir | Relato: muchos casos; inventario no inspeccionado. | Revisar muestra del flujo elegido y conservar IDs. |
| P-08 | Después: ¿qué contiene el workbook y qué herramientas MCP usan realmente? | Abierta | Por definir | Existencia por relato; contenido/instalación no inspeccionados. | Pedir versión y demostración en reunión. |
| P-09 | Después: ¿cómo se generan, versionan y validan las notas de Obsidian? | Abierta | Por definir | Método relatado; notas/prompt no inspeccionados. | Ver muestra, fuentes y conflictos con caso legacy. |
| P-10 | Después: ¿qué licencias/permisos y edición/versión de Azure habilitan el piloto? | Abierta | Por definir | Falta revisión de acceso y operaciones necesarias. | Identificar responsable de Azure y verificar alcance. |
| P-11 | Después: ¿cuánto cuestan revisión, intermitencia y mantenimiento hoy? | Abierta | Por definir | Sin mediciones ni línea base. | Registrar ejemplos y acordar medición comparable. |

La prioridad ordena el aprendizaje, no obliga a responder todo en una reunión. Agregá preguntas nuevas con IDs estables; no renumeres las referencias existentes.

## Próxima acción

**Propuesta pendiente de coordinar:** acompañar a una persona de QA en una sesión real usando las diez preguntas esenciales. Responsable y fecha: por definir. Salida inicial: nota con evidencia, recorridos parciales manual/automático y dudas priorizadas. Meta propuesta de primera semana: validar ambos mapas con QA, identificar quién confirma lo correcto con negocio/producto, asignar responsables a preguntas pendientes y elegir un problema prioritario para un piloto. No se contactó al equipo desde este trabajo.

## Cómo registrar una respuesta o confirmar una propuesta

1. Agregar respuesta/decisión, persona o rol, fecha, alcance y enlace a reunión con minuto/sección o evidencia técnica.
2. Cambiar pregunta a “respondida” solo dentro de ese alcance; si la respuesta es parcial, usar “parcial” y conservar lo faltante.
3. Cambiar propuesta a “confirmada” cuando su responsable la acepte, indicando qué confirma. Mantener “implementación pendiente” si aún no se ejecutó.
4. Si cambia una decisión, marcarla “revisada” o “reemplazada” y enlazar la nueva; conservar historia y motivo.
5. Actualizar ficha y mapa relacionados, y dejar una próxima acción con responsable y fecha acordada o “por definir”.

## Historial de cambios

| Fecha | Cambio | Fuente y límite |
| --- | --- | --- |
| 05/10/2026 | Registro inicial y guía de relevamiento creados. | Contexto del usuario y revisión de material local; sin reuniones ni acceso a sistemas del equipo. |
