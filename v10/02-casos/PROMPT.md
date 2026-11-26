# Etapa 02 · Diseñar y publicar casos de QA

Ejecutá este flujo desde el directorio que contiene `v10/`. Usá la entrega completa del 01 y conservá los IDs y superficies que QA definió.

```text
ENTREGA_ANALISIS = [carpeta con reglas.json, encargo.json y entrega.json]
DOCUMENTACION_FUNCIONAL = [manuales, historias, adjuntos o rutas, opcional]
PERFIL_QA = [URL, permisos, controles, actores, operaciones y modo de acceso aprobados]
AREA_QA = [ruta de área de trabajo que debe figurar en el CSV]
DATOS_Y_PERMISOS = [fixtures, capacidades habilitadas, modelos, estados visibles y limpieza aprobada si aplica]
```

## Leer y preparar

Leé `encargo.json`, `reglas.json` y las citas pertinentes. Si hay adjuntos funcionales, recuperá los fragmentos de los recorridos priorizados. Repetí `--documento-funcional` o `--consulta` según corresponda. Si el mismo documento está en ambas fuentes, conservá sus citas pertinentes y una sola identidad documental.

```sh
python v10/02-casos/scripts/documentacion.py procesar --id ID-fuentes --analisis "ENTREGA_ANALISIS" --documento-funcional "ARCHIVO"
```

Si necesitás archivos sintéticos, generalos con `mockups.py` a partir de una [especificación](ejemplos/mockup.demo.json). Elegí JSON para cuerpos API. Para adjuntos podés generar TXT, CSV, Markdown, HTML, DOCX, XLSX o PDF. La entrega registra semilla, huellas y estructura. Para un límite de tamaño, verificá los bytes efectivos de cada fixture antes de diseñar el caso. Los recursos persistentes en el producto requieren preparación y limpieza aprobadas.

```sh
python v10/02-casos/scripts/mockups.py procesar --id ID-fixture --spec "ESPECIFICACION" --nombre documento-qa --formato txt --semilla 42
```

## Diseñar y publicar

- Usá el [diseño de ejemplo](ejemplos/diseno.demo.json). Cada caso lleva un ID estable, el recorrido en `requirement`, precondiciones, una acción por paso, un `step_expected` verificable y fuentes. Para una cita funcional indicá `origen: funcional`, archivo, rango y frase. Si resuelve una regla pendiente, completá `aclaracion_funcional`.
- Para frontend, declará `via: playwright`, `browser_flow: web_ui`, acciones en `browser_steps` y selectores específicos. Para UI autenticada, declarale al perfil la sesión, el click de login, el método y la ruta, el control listo y, si corresponde, una sonda breve. Vinculá el caso con `browser_setup`. Para pruebas dedicadas de login o logout usá una sesión nueva con `browser_session: fresh`. [Contrato Playwright de V10](../03-ejecuciones/PERFIL-PLAYWRIGHT.md)
- Para chat, seleccioná el modelo y comprobalo con `verify_model` antes de enviar. Capturá la cantidad de turnos del asistente con `capture_count`, enviá el mensaje y apuntá `scope` al turno nuevo. Esperá la señal de fin de generación cuando exista. En seguimiento, repetí la captura y usá en la segunda pregunta un dato del primer turno.
- Declarale al runner los estados previos que pueda comprobar con `browser_preconditions`. Para variantes de funciones habilitadas o deshabilitadas, citá de dónde se obtiene el estado y asociá su indicador visible. En adjuntos, separá por formato y condición. Para un límite, diseñá el valor permitido y el primer valor excedido con fixtures distintos. Comprobá el resultado funcional o el error específico. Para descargas, afirmá extensión, tamaño y contenido representativo con `download_file.contains`. Registrá cada variante con `variante`.
- Para API, declará método, ruta y actor permitidos, y criterios sobre la respuesta de esa operación. Para DB, usá las lecturas aprobadas. Si una tarea tiene ambos recorridos, generá casos para cada superficie. En UI indicá `value_env` para el acceso. En API y DB usá los nombres de variables del perfil. El ejecutor los resuelve desde `v10/credenciales.txt` o su entorno.
- Si falta un requisito, registrá el recorrido en `pendientes` con `categoria`, `motivo` y `siguiente_accion`. Categorías disponibles `regla`, `fixture`, `acceso`, `capacidad`, `limpieza`, `runner`, `prioridad` y `otro`.

```sh
python v10/02-casos/scripts/preparar.py procesar --id ID-casos --analisis "ENTREGA_ANALISIS" --diseno "DISENO" --area-qa "AREA_QA"
```

Agregá `--contexto-funcional RUTA_FUENTES` y `--mockups RUTA_FIXTURE` cuando se hayan generado. Repetí `--mockups` para más entregas. Usá rutas `fixtures/nombre.ext` en cuerpos API y el nombre relativo de la fixture en `upload`.

Si el validador informa citas inválidas, corregí todas las filas de `citas-invalidas.json` con el extracto y el rango que correspondan. Revisá la ruta de área, los casos por superficie y los pendientes. Entregá la carpeta publicada con `casos-qa.csv`, `suite.json` y `entrega.json`. El exportador `exportar_azure.py` fija encabezados, orden, formato y valores por defecto de QA. Si cambia el contrato de Azure Test Plans, ajustá ese script y probá el archivo antes de entregar. Con telemetría, usá `preparar.py medir` y revisá `metricas-etapa.json`. Cerrá con `log02.md` incluyendo los IDs de recuperación funcional, fixtures, fallos y publicación usados.

```sh
python v10/02-casos/scripts/preparar.py consolidar --id ID-fuentes --id ID-fixture --id ID-casos
```
