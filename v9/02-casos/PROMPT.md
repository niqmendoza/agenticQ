# Etapa 02 · Diseñar y publicar casos de QA

Ejecutá este flujo desde el directorio que contiene `v9/`. Usá la entrega completa del 01 y conservá los IDs y superficies que QA definió.

```text
ENTREGA_ANALISIS = [carpeta con reglas.json, encargo.json y entrega.json]
DOCUMENTACION_FUNCIONAL = [manuales, historias, adjuntos o rutas, opcional]
PERFIL_QA = [URL, permisos, controles, actores, operaciones y modo de acceso aprobados]
AREA_QA = [ruta de área de trabajo que debe figurar en el CSV]
DATOS_Y_PERMISOS = [fixtures, capacidades habilitadas y limpieza aprobada si aplica]
```

## Leer y preparar

Leé `encargo.json`, `reglas.json` y las citas pertinentes. Si hay adjuntos funcionales, recuperá los fragmentos de los recorridos priorizados. Repetí `--documento-funcional` o `--consulta` según corresponda. Si el mismo documento está en ambas fuentes, conservá sus citas pertinentes y una sola identidad documental.

```sh
python v9/02-casos/scripts/documentacion.py procesar --id ID-fuentes --analisis "ENTREGA_ANALISIS" --documento-funcional "ARCHIVO"
```

Si necesitás archivos sintéticos, generálos con `mockups.py` a partir de una [especificación](ejemplos/mockup.demo.json). Elegí JSON para un cuerpo de API, CSV para registros o TXT, Markdown, HTML o DOCX para adjuntos. La entrega conserva la semilla y la huella del fixture. Los datos de producto que requieren preparación en QA, como una base accesible o un chat de referencia, necesitan un recurso aprobado y un plan de limpieza.

```sh
python v9/02-casos/scripts/mockups.py procesar --id ID-fixture --spec "ESPECIFICACION" --nombre documento-qa --formato txt --semilla 42
```

## Diseñar y publicar

- Usá el [diseño de ejemplo](ejemplos/diseno.demo.json). Cada caso lleva un ID estable, el recorrido en `requirement`, precondiciones, una acción por paso, un `step_expected` verificable y fuentes. Para una cita funcional indicá `origen: funcional`, archivo, rango y frase. Si resuelve una regla pendiente, completá `aclaracion_funcional`.
- Para frontend, declará `via: playwright`, `browser_flow: web_ui`, acciones en `browser_steps` y selectores estables y específicos. Para chat, esperá el mensaje nuevo y el fin de la generación. Comprobá su texto con `control_text` o `control_contains` sobre el mensaje del asistente. Si probás seguimiento, hacé que la segunda pregunta dependa de un dato del primer turno. Para adjuntos, usá un selector único, esperá el estado de procesamiento y verificá un valor presente en el fixture. Para descargas usá un paso `download` y el criterio `download_file` con su ID, extensión y tamaño mínimo.
- Para API, declará método, ruta y actor permitidos, y criterios sobre la respuesta de esa operación. Para DB, usá las lecturas aprobadas. Si una tarea tiene ambos recorridos, generá casos para cada superficie. En UI indicá `value_env` para el acceso. En API y DB usá los nombres de variables del perfil. El ejecutor los resuelve desde `v9/credenciales.txt` o su entorno.
- Si falta un requisito, registrá el recorrido en `pendientes` con `categoria`, `motivo` y `siguiente_accion`. Categorías disponibles `regla`, `fixture`, `acceso`, `capacidad`, `limpieza`, `runner`, `prioridad` y `otro`.

```sh
python v9/02-casos/scripts/preparar.py procesar --id ID-casos --analisis "ENTREGA_ANALISIS" --diseno "DISENO" --area-qa "AREA_QA"
```

Agregá `--contexto-funcional RUTA_FUENTES` y `--mockups RUTA_FIXTURE` cuando se hayan generado. Repetí `--mockups` para más entregas. Usá rutas `fixtures/nombre.ext` en cuerpos API y el nombre relativo de la fixture en `upload`.

Revisá la ruta de área, los casos por superficie y los pendientes. Entregá toda la carpeta publicada con `casos-qa.csv` de 13 columnas, `suite.json` y `entrega.json`. Con telemetría, usá `preparar.py medir`. Cerrá con `log02.md` incluyendo los IDs de recuperación funcional, generación de fixtures, fallos y publicación usados.

```sh
python v9/02-casos/scripts/preparar.py consolidar --id ID-fuentes --id ID-fixture --id ID-casos
```
