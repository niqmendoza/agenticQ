# Prueba de Qwen pequeño en esta Mac

29/10/2026. Se instaló y ejecutó **Qwen3.5:0.8b-q8_0**, no Qwen3.8. También se probó `qwen3.5:4b`, ya instalado. No se actualizó Ollama, no se descargó Saluki ni se modificaron parámetros globales. Todo el contexto documental se procesó por la API local.

**Resultado:** el 0.8B corre con holgura para este ensayo corto, pero los buenos fragmentos de entrada no bastaron para producir casos confiables. La capa de scripts actual recupera, limita y verifica evidencia; todavía no decide todas las reglas y combinaciones que hay que probar.

## Comparación acotada

Se usaron fragmentos nativos conservados de las pruebas de RAGFlow. Se eligieron deliberadamente fuentes que contienen la regla para aislar al generador, sin una búsqueda en vivo. Las tareas fueron: restricciones de usuarios, una sugerencia contraria a la vigencia de URLs firmadas y un cierre de sesión de quince minutos que no estaba documentado.

| Configuración | Modelo | JSON completo | Cortado por longitud | Memoria de Ollama muestreada | Se abstuvo ante la regla ausente |
|---|---|---:|---:|---:|---|
| Inicial | qwen3.5:0.8b-q8_0 | 1/3 | 2 | 1.02 GiB | No |
| Inicial | qwen3.5:4b | 3/3 | 0 | 2.96 GiB | Sí |
| Ajustada | qwen3.5:0.8b-q8_0 | 3/3 | 0 | 1.02 GiB | No |
| Ajustada | qwen3.5:4b | 3/3 | 0 | 2.96 GiB | Sí |

La memoria es el mayor valor de `size` informado por `/api/ps` durante el muestreo; no es el pico total de la Mac ni una garantía para contextos más largos. El contexto configurado fue de 4.096 tokens, con salida limitada a 1.200. Las respuestas registraron entre 845 y 854 tokens nativos de entrada. RAGFlow permaneció encendido durante las generaciones.

## Hallazgos concretos

- El 0.8B produjo inicialmente un JSON con citas reales, pero supuso que un usuario `pending` ya tenía acceso a la vista de chat. La fuente dice que sólo ve la pantalla de espera. También agregó acciones de audio y video no justificadas para el caso.
- Con el ajuste completó los JSON, pero inventó identificadores de fragmento y no se abstuvo ante los quince minutos sin respaldo. Formato válido no equivale a un caso correcto.
- El 4B se abstuvo en las dos configuraciones ante la regla ausente. En la consigna de URLs, la primera configuración aceptó un esperado contrario a la fuente; la segunda reconoció la regla, aunque agregó un código HTTP no solicitado y dejó pasos por corregir.
- El control de citas es literal y estricto: algunas diferencias del 4B son comillas añadidas o formato HTML; otras son paráfrasis. Se conservaron las salidas originales para distinguir estos problemas de una referencia inventada.

La configuración inicial usó temperatura cero y sin penalización de presencia. Después de observar repetición se congeló una segunda configuración con [los parámetros de texto recomendados por Qwen](https://huggingface.co/Qwen/Qwen3.5-0.8B#best-practices) y límites de longitud/cantidad en el esquema. Se cambiaron dos aspectos a la vez; no se aisló el efecto de cada uno. Los límites del esquema también pueden recortar una frase dentro de un JSON válido.

## Decisión para el piloto

No adoptar el 0.8B como diseñador de casos con estas configuraciones. Se puede evaluar para una tarea más restringida y comprobable por código. El 4B es un candidato más útil para un siguiente ensayo con QA, pero tampoco está aprobado para generación autónoma. No se publicaron los resultados en Azure y ningún caso se dio por aprobado.

Son tres tareas conocidas, una muestra por modelo/configuración, con revisión documental del asistente y sin revisión independiente de QA. Los modelos también usan cuantizaciones distintas (0.8B Q8 y 4B Q4); no es una comparación causal pura de cantidad de parámetros ni una conclusión universal sobre la familia Qwen.

## Evidencia y reproducción

- `small-model-cases.json`: primer protocolo.
- `small-model-tuned-cases.json`: segundo protocolo, con los mismos casos.
- `results/2026-10-29-small-v1/` y `results/2026-10-29-small-tuned-v1/`: solicitudes, texto final, métricas nativas, identidades de los modelos y manifiestos.
- `small-model-review.json`: observaciones documentales; aprobación de QA pendiente.

Desde `Post Harness V2`, con los dos modelos ya instalados:

```sh
"../Post Harness/.venv/bin/python" ollama-pilot/evaluate_small_models.py \
  --protocol ollama-pilot/small-model-tuned-cases.json \
  --out ollama-pilot/results/NUEVO-ENSAYO
```

El evaluador sólo llama al servidor local, conserva carpetas nuevas y no descarga modelos. Las respuestas se guardan con su contenido final y métricas; no se guarda el campo de razonamiento interno del modelo. Las verificaciones de JSON/citas no evalúan el respaldo semántico del caso. Se comprobaron además controles del evaluador para JSON inválido, cita no literal y abstención.

Fuente de la variante instalada: [Ollama · Qwen3.5 0.8B Q8](https://ollama.com/library/qwen3.5:0.8b-q8_0).
