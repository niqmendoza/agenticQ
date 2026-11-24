# Etapa 2 · Diseñar y publicar casos de prueba

Copilot, usá la terminal desde la carpeta que contiene `v8/`, con el Python del proyecto. Completá los marcadores con las rutas y los IDs reales. `preparar.py` es el paso obligatorio para publicar el CSV de QA y la suite ejecutable a partir del mismo diseño.

```text
ENTREGA_ANALISIS = [carpeta cerrada con reglas.json y entrega.json]
DOCUMENTACION_FUNCIONAL = [adjuntos o rutas, opcional]
PERFIL_QA = [controles, actores, rutas y operaciones autorizadas]
AREA_QA = [ruta de área para el CSV]
```

## Incorporar las fuentes de la tarea

Leé `encargo.json`, `reglas.json` y las citas pertinentes. Si QA aportó documentación funcional, ejecutá `documentacion.py` antes de diseñar. Repetí `--documento-funcional` por archivo. El script busca en función de los recorridos. Usá `--consulta` para una búsqueda puntual. Si el campo está vacío, diseñá con los extractos del segundo cerebro.

```sh
python v8/02-casos/scripts/documentacion.py procesar --id ID-fuentes --analisis "ENTREGA_ANALISIS" --documento-funcional "ARCHIVO"
```

Leé `documentacion-funcional.json` y los extractos relevantes. Usalos para describir cómo trabaja el usuario, qué variantes importan y qué resultado puede observar. Citá el texto extraído con `{"origen":"funcional","path":"guia.md","start":12,"end":13,"locator":"frase documentada"}`. Si la guía resuelve una regla pendiente, incluí la cita y `aclaracion_funcional`. Si falta respaldo o dos fuentes vigentes se contradicen, registrá en `pendientes` el ID del recorrido, las referencias y la pregunta.

## Diseñar y validar

Armá el JSON a partir del [diseño de ejemplo](ejemplos/diseno.demo.json).

1. Conservá el ID del recorrido en `requirement` y un ID estable por caso. Escribí el título funcional, las precondiciones, una acción por paso y un `step_expected` verificable por acción. Completá el área y los campos de QA. Cada recorrido debe quedar cubierto por casos ejecutables o tener un motivo en `pendientes`.
2. Para frontend, registrá el caso en `pasos` con `via: playwright` y definí `browser_flow: web_ui`, acciones en `browser_steps` y comprobaciones visibles en `criteria`. Usá controles conocidos del entorno o de pruebas existentes. Cada caso comienza en una sesión aislada. Incluí autenticación cuando corresponda, variables de entorno para los secretos y las operaciones permitidas que la pantalla necesita. Para API o DB, usá la superficie fijada en el encargo.
3. Citá la evidencia de cada esperado. Guardá los datos sintéticos bajo `fixtures/` junto al diseño y referenciá los archivos y contratos aplicables.

```sh
python v8/02-casos/scripts/preparar.py procesar --id ID-casos --analisis "ENTREGA_ANALISIS" --diseno "DISENO"
```

Agregá `--contexto-funcional "RUTA_ENTREGA_FUNCIONAL"` si consultaste los adjuntos. El script valida las referencias, el diseño y la preparación de los pasos de Playwright. Si detecta un problema, corregí el JSON y volvé a ejecutar. La entrega oficial se genera con este comando. Usá `draft_cases.py` solo si el encargo pide un piloto de borradores con Ollama.

Verificá que la carpeta publicada contenga `casos-qa.csv` con las 13 columnas de QA, `suite.json` y `entrega.json`. Pasá esa carpeta completa al ejecutor junto con los pendientes y el `resumen.json` del intento. Con telemetría nativa, registrá el corte con `preparar.py medir`. [Medición por etapa](../README.md#logs-consumos-y-repetición)
