# Medición de tokens por etapa

El objetivo es registrar el consumo del agente durante la iteración, con una fuente verificable y sin confundirlo con el tamaño de los documentos leídos. Esta guía define qué solicitar; **V3 no extrae automáticamente el consumo de Copilot ni garantiza que su entorno lo exponga**.

## Etapas y límites

1. **Lectura y análisis:** consultas al segundo cerebro, ampliaciones y análisis del contexto.
2. **Generación de casos:** diseño, revisión y registro del plan de pruebas.
3. **Ejecución de pruebas:** interacción con herramientas, análisis de resultados y registro de hallazgos.
4. **Otras actividades:** preparación, coordinación, cierre o trabajo que no encaja en las etapas anteriores. Una respuesta que abarque varias etapas se registra aquí como `mixta` si el proveedor no permite repartir su consumo con evidencia.

Al inicio y cierre de cada etapa registrar hora, herramientas/modelo conocidos, fuente de telemetría y referencia verificable. Usar únicamente contadores nativos que el entorno exponga de forma autorizada. Si el contador es acumulado, guardar cortes comparables y calcular la diferencia únicamente cuando su alcance sea idéntico y no se reinicie. Si hay consumo por respuesta, contabilizar cada respuesta una vez mediante su identificador o referencia verificable. No sumar cortes acumulados ni el total del turno sobre las mismas respuestas. Cuando no sea posible asignar una respuesta a una sola etapa, dejarla como mixta; no repartirla por tiempo o porcentaje supuesto.

## Campos y reglas

Copiar [`examples/metricas-tokens.example.json`](../examples/metricas-tokens.example.json) a la carpeta de sesión como `metricas-tokens.json` y completar con valores medidos. Los campos desconocidos son `null`, no cero. En cada etapa indicar `estado` (`medido`, `parcial`, `no_disponible` o `no_aplica`), `fuente`, `alcance`, `modelo`, inicio/fin, identificadores o evidencia y los siguientes valores cuando estén disponibles:

- `entrada`: tokens de entrada del modelo; `salida`: tokens de salida. `total` es entrada + salida solo cuando ambos están disponibles y corresponden al mismo alcance; de lo contrario `null` o total nativo explícitamente identificado.
- `entrada_cacheada` y `razonamiento`: registrar por separado cuando el proveedor los informe, junto con su semántica. Si el proveedor indica que son subconjuntos de entrada y salida, respectivamente, **no sumarlos otra vez**. No asumir esta semántica si el proveedor no la documenta o expone.
- `total_iteracion`: reportar como completo solo si abarca todo el trabajo y cada respuesta se cuenta una vez, incluidas preparación, coordinación, llamadas mixtas y cierre. Si la medición es parcial, presentar como subtotal observado y describir lo que falta; no sumar subtotales que se solapen.
- Si hay modelos o proveedores distintos, conservar el desglose por modelo y fuente. Uso nativo de un modelo llamado por la aplicación bajo prueba va separado del consumo del agente; no se presume disponible ni se mezcla en el total del agente.

El procesamiento local de Python, Playwright o las API no genera por sí mismo tokens de modelo: registrar duración, llamadas o errores como métricas de herramientas, por separado. El tamaño del texto recuperado puede medirse como **estimación documental** con un tokenizer explícito, versión y alcance, si está disponible; es un indicador diferente del uso nativo y no se suma al mismo. No convertir tokens a dinero sin tarifas y detalle verificables.

Registrar en `log.md` una nota por etapa con estado, cifras disponibles y ruta al archivo de métricas usando `record`; no editar el log generado. El informe final debe incluir tabla por etapa, total completo o subtotal marcado, fuente y limitaciones. Si la plataforma no expone telemetría, dejar `no_disponible` y continuar la prueba: no estimar por cantidad de palabras ni presentar una suposición como medición.

## Comparación con el histórico

El informe anterior usa consumo nativo acumulado del turno, no solo texto recuperado. Para comparar V3, anotar modelo, herramienta, alcance, número de respuestas y etapas incluidas. Una ejecución distinta, otro modelo o un alcance diferente no constituye comparación causal ni permite afirmar ahorro general. Mantener separados mediciones nativas, estimaciones de contexto y uso de modelos de la aplicación.
