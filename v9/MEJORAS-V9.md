# Cambios de V9 a partir de la corrida de V8

| Módulo | Mejora | Beneficio esperado |
|---|---|---|
| 01 · Alcance | Campos de superficie, prioridades, autenticación esperada y build. IDs separados para UI y API. | Detectar ambigüedades antes de buscar evidencia y conservar el alcance entre agentes. |
| 01 · Validación | Nombre visible separado de `app_id`. Comando `--validar-encargo`. | Evitar rechazos por espacios o puntos en el nombre y diagnosticar entradas antes de indexar. |
| 01 · Citas | Ampliar rangos desde el índice conservado con verificación de revisión. | Preparar una cita faltante sin volver a indexar ni ampliar todas las consultas. |
| 02 · Documentación | Identificar originales repetidos por SHA-256 y deduplicar referencias al mismo rango. | Mantener trazabilidad y evitar dos citas equivalentes al mismo fragmento. |
| 02 · Diseño | Área de QA confirmada, pendientes categorizados y conteos por superficie. Criterios asociados a controles en frontend. | Detectar CSV mal clasificados y saber qué hace falta para habilitar casos. |
| 02 · Fixtures | `mockups.py` genera JSON, CSV, TXT, Markdown, HTML y DOCX reproducibles. `preparar.py --mockups` incorpora la entrega cuyo hash fue validado. | Generar archivos de prueba portables y repetir los mismos datos con la semilla. |
| 03 · Acceso | `credenciales.txt` privado y variables por caso. Los secretos se cargan exclusivamente para ejecutar. | Reducir pedidos repetidos y evitar valores en prompts, diseños y reportes. |
| 03 · Preflight | Diagnóstico sin casos, conectividad TCP, dependencias por canal y referencia de build. | Resolver varios problemas al principio y ejecutar los casos listos aunque otra superficie esté bloqueada. |
| 03 · Playwright | Diagnóstico de selectores, comprobaciones de texto acotadas, espera de fin de generación y evidencia de descarga. | Reducir falsos aprobados y saber si el problema está en el selector, el entorno o el esperado. |
| 03 · Dictamen | Alcance, casos y cobertura por superficie. HTTP de navegación y operación con rótulos propios. | Interpretar correctamente un JUnit verde con recorridos pendientes. |
| Todas · Logs | `log01.md`, `log02.md` y `log03.md` con anexos textuales, copias deduplicadas y huellas de binarios. Corte nativo opcional con `medir`. | Revisar una corrida por módulo desde un archivo y comparar indicios de costo cuando exista telemetría. |
