# Telemetría encontrada tras finalizar las evaluaciones

El protocolo congelado antes del ensayo decía que las herramientas de colaboración no exponían usage. Esa observación sobre la interfaz seguía siendo cierta, pero después de congelar las entregas se encontró telemetría nativa en los rollouts locales de ambas sesiones. Se conserva el protocolo original y se agrega esta corrección, sin editar entregas ni reoptimizar la recuperación.

La documentación oficial de Codex App Server describe `thread/tokenUsage/updated`: https://learn.chatgpt.com/docs/app-server . La guía de observabilidad describe tokens de entrada, caché, salida y razonamiento: https://developers.openai.com/api/docs/guides/agents-api/observability . Los formatos del rollout local no son una API estable prometida. Se usaron como evidencia local de esta versión, sin abrir credenciales ni hacer llamadas autenticadas nuevas.

`extract_usage.py` identifica turnos por sus IDs, deduplica response_id y suma sólo `usage` por respuesta. NO suma snapshots acumulativos `turn_token_usage`; únicamente los contrasta con el resultado sumado. `cached_input_tokens` está incluido en `input_tokens`, y `reasoning_output_tokens` en `output_tokens`. `total_tokens = input_tokens + output_tokens`. El exportado guarda números, timestamps, modelo/esfuerzo, IDs de turno y hashes; no copia razonamiento, mensajes, secretos ni credenciales del rollout.

La comparación principal usa el primer turno completo de cada evaluador: 21 respuestas de modelo cada uno, gpt-6.1-sol / high. El segundo turno de scripts fue una aclaración posterior de cómo se imprimió stdout, sin modificar entregables; sus 97.711 tokens registrados se exponen aparte y se excluyen del ensayo principal. El mensaje del coordinador durante el turno de scripts sólo pidió explicar relecturas y transformaciones; no compartió casos o fuentes nuevas. Se cuenta como intervención asimétrica y posible sesgo de observación.

Además se exportan payloads visibles de herramientas en `*/presentado` y sus conteos con o200k_base en `transcript-conteos.json`. No se exportan instrucciones system/developer ni razonamiento cifrado. Las categorías de contenedor JSON usan serialización compacta como proxy; los strings crudos se conservan. Ese conteo una vez no reemplaza el uso acumulado nativo.

## Corrección del conteo documental inicial
Las 52 salidas nativas de brain.py suman 59.437 tokens, pero las últimas 21 NO se mostraron completas al modelo. Python capturó el JSON y sólo imprimió una línea JSON `path/headings` por archivo. El borrador de resultado que se leyó dentro de Python tampoco se imprimió. Contar cada archivo *.result.json como contexto del LLM exageraría la entrada.

El stdout transformado se reconstruye fielmente según aclaración del evaluador en `scripts/lecturas/revision-citas-presentada.txt`; el registro real del shell también está en `scripts/presentado`. Las primeras 31 salidas se mostraron completas. El corpus procesado fuera del LLM se contabiliza separado del documental presentado. No se descartan las relecturas para mejorar el porcentaje: se cuentan los encabezados que se presentaron y las llamadas locales que se hicieron.

No hubo pruebas de aplicación. Los números de usage son telemetría registrada, no una factura ni un precio. El ahorro de entrada cacheada domina la diferencia del total; la entrada no cacheada y la salida aumentaron. Una reducción de contexto no garantiza menor costo monetario.
