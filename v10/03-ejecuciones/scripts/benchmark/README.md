# Evaluación de modelos · QA V10

Modo opcional para comparar modelos de Copilot con el mismo trabajo de QA. Cada corrida genera sus notas del CLI avanzado, la evidencia por intento, el log, los tokens de entrada y salida por etapa y el modelo observado en cada llamada. El comparador agrega una revisión independiente de lo que el modelo entendió, diseñó y ejecutó.

## Preparar una comparación

1. Completá una copia de [benchmark.ejemplo.json](benchmark.ejemplo.json) y redactá una consigna Markdown con los datos del [alcance del encargo](../../../01-analisis/PROMPT.md). Anotá el build y el entorno exactos. Fijá el estado inicial y cómo restaurarlo, los datos, la semilla si aplica, el cliente, los permisos, los límites y los recorridos obligatorios. En cada etapa de la rúbrica, describí puntos del producto que se puedan comprobar con evidencia. Mantené la rúbrica fuera del material que va a leer el agente.
2. Para evaluar la lectura del segundo cerebro, usá la misma copia de solo lectura del corpus en todas las corridas. El comando `v10/03-ejecuciones/scripts/qa.py index --run ID` imprime la ruta del artefacto JSON. El campo `revision` de ese archivo identifica el corpus. Podés obtenerlo en una sesión auxiliar de `qa.py` sin hacer pruebas. Si el encargo prescinde del corpus textual, usá `null` y adaptá los puntos de análisis a las fuentes disponibles.
3. Congelá la consigna y la configuración. Ejecutá desde la carpeta que contiene `v10/`.

```sh
python3 v10/03-ejecuciones/scripts/benchmark/evaluate.py congelar --config benchmark.json --consigna consigna.md
```

El script registra hashes de la consigna y del harness y verifica la revisión del corpus que usó cada sesión. El build, el entorno y los recorridos deben coincidir. El equipo que ejecuta controla el estado inicial real, los fixtures, los permisos y los ajustes del cliente, que quedan declarados en la configuración. Si cambian las condiciones, congelá otro ID.

## Una conversación por corrida

1. Restaurá el estado inicial. Configurá la [telemetría de Copilot](../../MEDICION-TOKENS.md) en un archivo exclusivo y privado. Seleccioná el modelo en el cliente. Usá una etiqueta de carpeta como `Qwen`, `GPT-6.1-Sol` o `Sonnet` y el ID exacto de respuesta del proveedor. La etiqueta sirve para identificar la corrida.
2. Abrí una conversación nueva. Pasale el [instrucciones de evaluación](INSTRUCCIONES.md), la misma consigna congelada. La comprobación usa `gen_ai.response.model` para OpenTelemetry o `model` en un JSONL nativo normalizado. Un ID solicitado en la configuración del cliente solo sirve como dato de entrada. Si la fuente omite el ID devuelto, usá otra exportación nativa que sí lo informe.
3. Cuando Copilot haya marcado el cierre y el exportador termine de escribir, confirmá que la carpeta de la corrida exista. Si quedó pendiente por el corte de telemetría, corré desde la terminal con la conversación ya terminada:

```sh
python3 v10/03-ejecuciones/scripts/benchmark/evaluate.py archivar --run corrida-01
```

El archivo queda en `v10/03-ejecuciones/logs/qc/evaluate-llm/resultados/<benchmark>/modelos/<etiqueta>/<id-corrida>/`. La opción `--incompleta` conserva una corrida con bloqueos o datos faltantes y la deja fuera de los agregados. Cada corrida conserva su paquete Markdown con las evidencias enlazadas, el reporte gerencial HTML y un `medicion.json` compacto para el comparador. La telemetría original y las credenciales permanecen en el área privada. Los resultados locales se ignoran en Git.

## Revisar y comparar

Un revisor independiente verifica cada punto de la rúbrica y registra si se logró, por qué y dónde está la evidencia. En diseño y ejecución, relaciona los puntos logrados con los casos concretos. En ejecución, cada caso validado debe enlazar a evidencia de un intento observado. Un resultado funcional fallido puede demostrar que el modelo comprobó bien el escenario. Adaptá [revision.ejemplo.json](revision.ejemplo.json) a los IDs y evidencias de la corrida.

```sh
python3 v10/03-ejecuciones/scripts/benchmark/evaluate.py revisar --benchmark comparacion-qa-01 --modelo Qwen --id corrida-01 --archivo revision.json
python3 v10/03-ejecuciones/scripts/benchmark/evaluate.py comparar --benchmark comparacion-qa-01
```

Abrí `comparacion.html` en un navegador o copiá `comparacion.md` y su carpeta a Obsidian. Los gráficos muestran las medianas de consumo y de puntos logrados por etapa. La tabla agrega tiempos, casos validados y tokens por punto logrado. El tamaño de la muestra aparece junto a cada mediana. La comparación de calidad queda pendiente hasta reunir las revisiones. Las llamadas de identidad ausente o mixta dejan la corrida conservada fuera de los agregados. Repetí `comparar` a medida que se incorporen corridas y revisiones.

Para medir detección empírica en builds con regresiones conocidas, usá `v10/03-ejecuciones/scripts/qa.py score-models` con el [experimento de ejemplo](experimento.ejemplo.json).
