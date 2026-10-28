# Documentación viva de QA

**Actualización: 5 de octubre de 2026.**

Empezá por la [guía de relevamiento](Guia-relevamiento-QA.md). La tarea inmediata es aprender con QA cómo trabajan hoy y dejar ese proceso escrito. No necesitás conocer de antemano el runner ni elegir una plataforma.

| Archivo | Para qué usarlo |
| --- | --- |
| [Guía de relevamiento](Guia-relevamiento-QA.md) | Contexto, primeros pasos, vocabulario y cuatro diagramas del proceso actual parcial y de las propuestas. |
| [Entrevistas con QA](Entrevistas-QA.md) | Preguntas priorizadas y evidencias para pedir durante las reuniones. |
| [Registro de decisiones y preguntas](Registro-QA.md) | Pendientes, decisiones, fuentes y próxima acción. |
| [Plantilla de reunión](plantillas/Reunion-QA.md) | Separar relato, observación, interpretación y validación. |
| [Plantilla de proceso actual](plantillas/Proceso-AS-IS.md) | Documentar un proceso observado, sus excepciones y posibles mejoras. |
| [Propuesta previa](Proceso-QA-agentizada.md) | Material de referencia del 30 de septiembre, conservado íntegramente. |

La propuesta previa describe una arquitectura más amplia, con Azure Repos, Pipelines y un buscador de conocimiento. Esos componentes y conexiones **no están confirmados como implementación actual** por este relevamiento. Tampoco se inspeccionaron el workbook, las notas de Obsidian ni las herramientas instaladas del equipo. Para distinguir lo conocido hoy de lo propuesto, usá la guía nueva y el registro; si aparece una diferencia con material anterior, anotala con evidencia antes de resolverla.

## Cómo guardar lo que aprendamos

1. Copiá la plantilla de reunión a `reuniones/AAAA-MM-DD-tema.md` cuando ocurra una reunión. Los nombres son una convención propuesta; todavía no hay reuniones registradas.
2. Copiá la plantilla de proceso a `procesos/nombre-del-proceso.md` cuando haya pasos que documentar. Una ficha puede reunir varias reuniones.
3. Enlazá cada afirmación importante con su reunión y minuto de transcripción, caso, corrida u otra evidencia. Conservá la fuente original; una transcripción también puede contener errores.
4. Pedí a QA que revise la ficha. Registrá qué confirmó, qué corrigió y qué sigue pendiente, con fecha y alcance.
5. Actualizá el registro y luego el mapa actual. Actualizá las propuestas solo cuando el aprendizaje o una decisión lo justifique.

Los archivos son Markdown común: se pueden editar aquí o consultar desde Obsidian. Versionarlos es una propuesta para conservar cambios; no hay un repositorio Git en esta carpeta al momento de esta edición. Guardá referencias seguras a accesos y datos, nunca contraseñas, tokens ni payloads sensibles sin depurar.
