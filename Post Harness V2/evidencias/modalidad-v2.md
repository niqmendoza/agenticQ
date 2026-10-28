# Modalidad C — scripts V2, contexto limpio

Carpeta de entrega: /Users/nmendoza/Desktop/Code/QA agentizada/Post Harness V2/evidencias/evaluacion
No leer reportes anteriores, casos de otros evaluadores, código de scripts, índice SQLite, inventario, snapshot ni fuentes directamente. Toda evidencia documental se obtiene exclusivamente por stdout de brain.py V2. No navegar Internet, crear subagentes ni ejecutar la aplicación. No reindexar. No transformar ni recortar stdout: el registro de entrega sólo demuestra que el script devolvió esas líneas; debe coincidir con lo presentado. Si una herramienta trunca, registrarlo y volver a pedir un rango menor con --replay.

## Recuperación inicial
Ejecutar UNA operación pack con las mismas cinco preguntas fijadas en consultas-evaluacion.json; el archivo se pasa al script y no es necesario imprimirlo. Mantener estos parámetros iniciales; después ampliar libremente según evidencia insuficiente, sin objetivo obligatorio de ahorro.

'/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness/.venv/bin/python' '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness V2/scripts/brain.py' --db '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness V2/evidencias/indice.sqlite' --session '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness V2/evidencias/evaluacion/session.json' --log-dir '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness V2/evidencias/evaluacion/lecturas' pack --queries-json '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness V2/evidencias/consultas-evaluacion.json' --seeds 2 --related 5 --max-docs 20 --max-lines 120 --max-tokens 14000 --max-chars 50000

Usar functions.exec con max_output_tokens al menos 22000 y exec_command max_output_tokens al menos 20000 para este primer paquete. No imprimir lecturas extra del corpus para verificar.

## Interpretar el paquete y ampliar
- sources contiene path, SHA256, encabezados con líneas, total_lines y document_complete/missing_ranges. No confundir rango completo con documento completo.
- passages contiene source ID, start/end y texto con número de línea: N|texto literal. Las citas usan la ruta original indicada en sources, no el ID corto.
- pending muestra documentos/rangos no ampliados y motivos. pending_total y pending_list_truncated indican que la lista puede estar acotada. Revisar relaciones que puedan aportar restricciones y excepciones; no asumir cobertura por ranking o cantidad de notas.
- La sesión guarda intervalos devueltos. Repetir una consulta evita duplicar esos intervalos; --replay permite relectura explícita. No sustituye memoria del modelo ni garantiza que una herramienta no haya truncado.
- Para ampliar, misma base de comando: show 'ruta relativa' --start N --end M --max-lines 120 --max-tokens 5000 --max-chars 20000. Puede pedirse una nota relacionada por su ruta devuelta aunque no fuera semilla. links 'ruta' --limit 12 --offset 0 amplía relaciones paginadas. headings 'ruta' devuelve encabezados sin releer cuerpos. Repetir pack puede aportar intervalos pendientes; si sólo faltan relaciones, usar links/show de forma dirigida.

## Verificación final de estructura y referencias
Al guardar el resultado propio, ejecutar la misma base con verify '/ruta/resultado.json' --requirements-json '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness V2/evidencias/requirements.json' --save '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness V2/evidencias/evaluacion/verificacion.json'. Corregir rangos inválidos o no entregados usando sólo ampliaciones del script. El verificador informa etiquetas de sección, requisitos/criterios sin casos, duplicados exactos y oráculos pendientes. NO demuestra apoyo semántico ni calidad completa: revisar contenido de los esperados personalmente.
Podés añadir open_questions:[IDs] y oracle_status:pendiente a casos dependientes de decisiones, sin omitir los campos de la consigna común. No convertir un pendiente en pass/fail definitivo.

Conservar resultado.json, comportamiento.md y congelado.json como indica la consigna común. Todas las invocaciones se registran con --log-dir. Al terminar recuperación, avisar al coordinador sin compartir casos; continuar hasta congelar y no editar después. No se necesita calcular tokens.
