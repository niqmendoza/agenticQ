# Plantillas de V6

| Plantilla | Uso |
| --- | --- |
| [reporte-gerencial.html](reporte-gerencial.html) | HTML autocontenido que `export-html` completa con alcance, conteos, casos y hallazgos de la corrida. |
| [evaluacion.md](evaluacion.md) | Evaluación técnica que Copilot completa antes de publicar el informe Markdown. |
| [analisis.md](analisis.md) y [metricas.md](metricas.md) | Análisis de fuentes y registro de métricas. |
| [azure-test-cases.csv](azure-test-cases.csv) | Encabezados que usa `export-azure` para el CSV de Azure Test Plans. |
| [sdd-fix.md](sdd-fix.md) | Estructura de la propuesta que `export-fixes` genera por defecto confirmado y abierto. |

El CLI completa los campos `$variable` de las plantillas HTML y SDD. Copilot aporta los datos en el registro de la corrida. El CSV incluye una fila por paso, con acción y resultado esperado.
