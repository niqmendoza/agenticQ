# Adaptador de contexto · resultado del piloto v1

29 de octubre de 2026. RAGFlow local, mismo segundo cerebro; sin modelo generativo ni consumo de Copilot durante este ensayo.

**Se implementó y probó `scripts/retrieve.py`: entrega contexto compacto con fuentes, conserva el texto de los fragmentos y registra lo omitido.** El modo local `brain.py` y las evidencias anteriores se conservaron.

## Resultado medido

Se fijaron tres preguntas nuevas respecto del ensayo anterior: permisos de grupos, migraciones Alembic y aislamiento de búsquedas por recurso. Los seis controles documentales estaban definidos antes de consultar la API. Sigue siendo un corpus conocido, sin validación ciega de QA.

| Salida | Fragmentos | Tokens proxy | Señales documentales |
|---|---:|---:|---:|
| Respuestas nativas del cliente | 15, con dos repeticiones | 14.724 | Mismo contenido de origen |
| Paquete compacto sin recorte por presupuesto | 13 únicos | 8.667 | 6/6 |
| Primera entrega con límite de 6.000 tokens y 24.000 caracteres | 8 | 5.525 | 4/6 |
| Ampliación de esa entrega con la misma sesión | 5 restantes | 3.638 | 6/6 al reunir ambas entregas |

El paquete sin recorte redujo **41,1%** los tokens proxy frente al JSON nativo, preservando todos los fragmentos únicos. No se resumieron ni reescribieron sus textos. Las dos entregas acotadas sumaron 9.163 tokens: dividir también tiene un costo de metadatos. La primera entrega quedó en 18.188 caracteres y señaló sus cinco fragmentos pendientes.

El total nativo de RAGFlow incluyó otros 177 resultados fuera de las primeras páginas. Ningún perfil declara cobertura completa de la aplicación. Las seis señales son presencia de contenido en fuentes determinadas, no seis pruebas ejecutadas ni una evaluación semántica exhaustiva.

## Controles comprobados

- Texto e identidad de los 13 fragmentos únicos coinciden con las respuestas nativas capturadas; hashes verificados.
- Una repetición en la misma sesión no vuelve a entregar texto. `--replay` lo restaura.
- La interfaz CLI real guardó contexto y sesión, omitió repeticiones y volvió a entregar evidencia al solicitar replay.
- La suite completa pasó **43 tests**: modo local, cliente HTTP, presupuestos, fuente fuera de alcance, omisiones recuperables, cambios bajo el mismo chunk, integridad, fallos de escritura, consulta posterior fallida y bloqueo concurrente.
- Los archivos de contexto y sesión creados por la CLI tienen permisos privados. No se incluyeron claves ni encabezados en las evidencias.

## Límite que sigue abierto

La pregunta de control ajena al dominio devolvió cinco fragmentos de la aplicación. La compactación no resuelve ese problema: un resultado no prueba que el conocimiento responda la pregunta. QA o Copilot deben revisar el respaldo y conservar las dudas. Sigue pendiente evaluar el modelo/configuración de embeddings con un índice de comparación antes de cambiar el corpus de referencia.

Tampoco se midieron tokens nativos, créditos ni facturación de Copilot. Los números anteriores usan `tiktoken/o200k_base` sobre JSON serializado. No incluyen conversación, generación, caché ni reintentos del modelo.

## Archivos y reproducción

- [Guía de uso y contrato qa-context/1](../GUIA-CONTEXTO-RAGFLOW.md).
- Protocolo: `adapter-cases.json`.
- Ejecución completa: `pruebas/2026-10-29-adaptador-v1-completo/`.
- `native.json`: respuestas originales del cliente, sin claves.
- `full.compact.json`, `bounded.compact.json`, `continued.compact.json`: salidas exactas usadas para contar el contexto compacto.
- `summary.json`: métricas y señales; `MANIFIESTO.json`: hashes de las evidencias compartibles.
- `2026-10-29-adaptador-v1/` conserva el primer ensayo, anterior a agregar el control explícito de continuación.

Desde `Post Harness V2`:

```sh
"../Post Harness/.venv/bin/python" ragflow-local/evaluate_adapter.py \
  --out ragflow-local/pruebas/NUEVO-ENSAYO-ADAPTADOR

"../Post Harness/.venv/bin/python" scripts/verify_context.py \
  ragflow-local/pruebas/2026-10-29-adaptador-v1-completo/full.compact.json

"../Post Harness/.venv/bin/python" -m unittest discover -s tests -v
```

Cada ensayo requiere una carpeta nueva. Con otra recuperación pueden cambiar los resultados y las cifras; el protocolo y las respuestas quedan congelados para poder revisar cada ejecución.

El próximo ensayo útil es una tarea concreta del piloto con Copilot: recuperar contexto, ampliar donde falte respaldo, generar borradores citados y medir cuánto corrige QA. Recién después corresponde automatizar la publicación en Test Plans.
