# Borradores de casos con Qwen 4B · piloto local

El flujo conecta el contexto `qa-context/1` con `qwen3.5:4b` en Ollama y entrega JSON más Markdown para QA. Funciona en local y no necesita Copilot. La versión actual produce **borradores**, sin aprobarlos, ejecutarlos ni publicarlos en Azure.

## Qué cambió

Antes el modelo escribía pasos, esperados y citas libres. En el ensayo anterior eso permitió citas deformadas y esperados contrarios a las fuentes. Ahora hay dos llamadas:

1. **Seleccionar reglas.** El modelo recibe un catálogo con IDs cortos y distingue reglas encontradas, información ausente y conflicto entre fuentes. Una sugerencia del usuario se trata como una hipótesis, no como una nueva regla del producto.
2. **Proponer pasos.** Con las reglas seleccionadas, prepara hasta tres borradores funcionales. Elige el ID de la regla que respalda el esperado; el script copia su texto y resuelve las citas desde el contexto verificado.

Si falta la regla, no se hace la segunda llamada: se entrega una pregunta abierta. Si el modelo devuelve un JSON inválido, incompleto, con IDs inexistentes o campos de aprobación, la entrega falla explícitamente. No hay reintentos que oculten o reparen silenciosamente una salida inválida.

Esto comprueba trazabilidad e integridad. **No demuestra que el modelo eligió la regla adecuada ni que los pasos la prueben.** El campo `semantic_validation` conserva `not_performed`; QA revisa la selección, los pasos, los esperados y la cobertura.

## Uso por partes

Desde `Post Harness V2`, con RAGFlow y Ollama disponibles y `qwen3.5:4b` instalado:

```sh
"../Post Harness/.venv/bin/python" scripts/retrieve.py \
  --config ragflow-local/connection.json \
  --credentials-file ragflow-local/state/credentials.local.json \
  --application piloto \
  --session ragflow-local/state/tarea-casos-001.local.json \
  --query 'Roles de usuario pending pantalla de espera admin cambia rol user' \
  --page-size 2 --max-chars 24000 \
  --out ragflow-local/state/contexto-casos-001.local.json

"../Post Harness/.venv/bin/python" scripts/draft_cases.py \
  --context ragflow-local/state/contexto-casos-001.local.json \
  --task ollama-pilot/task.example.json \
  --model qwen3.5:4b \
  --out ollama-pilot/state/entrega-001
```

Editar una copia de `task.example.json` para cada tarea. Sus tres campos son:

```json
{
  "title": "Nombre de la tarea",
  "request": "Qué se quiere revisar o proponer; indicar las dudas y el alcance.",
  "max_cases": 2
}
```

`max_cases` admite de uno a tres. La consigna no certifica que una regla esté aprobada. Si llega un cambio funcional aprobado que contradice el segundo cerebro, actualizar o aportar su documentación de referencia; el generador no puede determinar por sí solo qué versión gobierna el producto.

## Qué deja la entrega

- `context.json` y `task.json`: entradas usadas.
- `trace.json`: ambas solicitudes, respuestas estructuradas y métricas nativas. No se guarda el razonamiento interno del modelo.
- `drafts.json`: contrato experimental `qa-drafts/1-experimental`, reglas, esperados y trazabilidad.
- `PARA-REVISION-QA.md`: los borradores, todas sus reglas citadas y observaciones para revisar.
- `failure.json`: si falla la operación después de crear la carpeta, conserva la traza disponible y el motivo. No contiene un borrador aprobado.

La carpeta de salida debe ser nueva. Los archivos se escriben con permisos privados y no se sobreescriben entregas anteriores. El cliente sólo permite un Ollama HTTP en loopback; una conexión remota necesita una integración propia. Las opciones del modelo se aplican por solicitud y no cambian la configuración global de Ollama.

## Cómo se conserva la evidencia

El script verifica primero los hashes y referencias del paquete. Después arma una vista legible, sin resumir: omite metadatos YAML, encabezados y secciones de enlaces relacionados; transforma las filas HTML en campos con sus encabezados. El catálogo conserva también el recorte crudo y su rango exacto de **caracteres dentro del fragmento**, más el hash del fragmento. No son líneas del archivo original ni una revisión del documento remoto.

El esperado es una **regla documental seleccionada**, que puede necesitar reformularse como comprobación observable antes de automatizar. Las reglas de apoyo aparecen también en el Markdown. `verify_result(contexto, borradores)` permite cotejar nuevamente el resultado contra el catálogo original; tampoco valida su significado.

Se rechaza un catálogo demasiado grande o una regla que exceda los límites del piloto, en lugar de cortarlos en silencio. Reducir el contexto mediante una consulta dirigida. Las omisiones de la recuperación se conservan en `context_omitted`; el total de resultados de RAGFlow no implica cobertura completa.

## Revisión de QA

Revisar, como mínimo, que la regla esté vigente, que corresponda al escenario y que los pasos permitan observar el resultado. Completar detalles de interfaz, datos y ambiente; comparar con casos actuales antes de crear duplicados. Corregir esperados demasiado generales y separar una duda de un caso ejecutable. Desarrollo permanece informado, sin una aprobación obligatoria de los casos.

La existencia de un Markdown no significa que el caso esté listo para Playwright. Tampoco se conectaron la consulta del catálogo de Azure, su publicación ni n8n.

## Pruebas y primer lote

[Resultado del ensayo](ollama-pilot/RESULTADO-GENERACION-4B.md) y [cinco borradores con pendientes señalados](ollama-pilot/PARA-REVISION-QA-4B.md).

Para repetir el protocolo de cuatro tareas en una carpeta nueva:

```sh
"../Post Harness/.venv/bin/python" ollama-pilot/evaluate_grounded_drafts.py \
  --out ollama-pilot/results/NUEVO-ENSAYO

"../Post Harness/.venv/bin/python" -m unittest discover -s tests -v
```

La suite ampliada tiene 57 tests. El modelo usa contexto de 8.192 tokens, salida acotada y dos configuraciones por etapa, registradas en cada traza. Se cuentan tokens nativos de Ollama; no son tokens ni créditos de Copilot. El tamaño del catálogo y la solicitud tienen límites de caracteres, que no garantizan equivalencia con el tokenizer del modelo.

Fuentes de la interfaz: [salida estructurada de Ollama](https://docs.ollama.com/capabilities/structured-outputs) y [Qwen3.5 4B](https://huggingface.co/Qwen/Qwen3.5-4B). Los parámetros se ajustaron para este ensayo; no se presentan como configuración óptima general.
