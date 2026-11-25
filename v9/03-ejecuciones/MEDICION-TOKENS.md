# Medición de tokens para evaluar modelos · V9

En el flujo de tres etapas, registrá cada conversación con el subcomando `medir` de su etapa. Los comandos `tokens-check` y `tokens-stage` de esta guía corresponden al CLI avanzado. Para el benchmark, inicializá con `init --benchmark`. [Medición de las tres etapas](../README.md#logs-consumos-y-repetición)

El harness usa los contadores de entrada y salida del cliente o del proveedor. El cálculo por etapa toma las llamadas individuales y excluye los agregados del mismo turno. La unidad de medición es una conversación exclusiva de QA, incluida la preparación de esa corrida.

## Preparar Copilot

Para Copilot CLI, configurá el archivo antes de iniciar la conversación. Desde la carpeta que contiene `v9/` podés usar una ruta de salida privada y distinta por corrida. [Referencia oficial de Copilot CLI](https://docs.github.com/en/copilot/reference/enterprise-administrators/opentelemetry-reference)

```sh
umask 077
mkdir -p .trabajo
export COPILOT_OTEL_FILE_EXPORTER_PATH="$PWD/.trabajo/copilot-qa.jsonl"
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT=NO_CONTENT
copilot
```

En VS Code, elegí la exportación a archivo compatible con el tipo de sesión. Para el exportador de Copilot Chat, buscá `github.copilot.chat.otel.enabled`, `github.copilot.chat.otel.exporterType` con valor `file` y `github.copilot.chat.otel.outfile` con una ruta absoluta. Para Agent Host, usá la configuración de exportación aplicable o la administrada por la organización. Mantené desactivada la captura de contenido. El archivo debe estar accesible desde el equipo donde corre el CLI de V9. [Configuración oficial de VS Code](https://code.visualstudio.com/docs/agents/guides/monitoring-agents)

Antes de ejecutar pruebas, generá un intercambio breve en la conversación de QA y esperá a que el exportador escriba el contador. Después de `init`, comprobá la fuente con el harness.

```sh
python3 v9/03-ejecuciones/scripts/qa.py tokens-check --run release-prueba --file .trabajo/copilot-qa.jsonl
```

Si el archivo contiene varias conversaciones, agregá `--scope` con el valor exacto de `gen_ai.conversation.id` de la conversación de QA. Los spans `chat` que solo indican el ID de traza se vinculan con el span raíz cuando este identifica la conversación. El CLI exige al menos una llamada con consumo positivo verificable y fija esa fuente para la corrida.

## Usar una exportación nativa del proveedor

Si el equipo ya dispone de un registro del proveedor, exportá solo las llamadas que se puedan atribuir a esta conversación. LiteLLM puede conservar el consumo por llamada en sus registros si está habilitado. Confirmá la correspondencia mediante identificadores propios de la corrida. Si el cliente usa llamadas internas fuera del proxy, el registro de LiteLLM cubre el tráfico de ese proxy. [Registro de consumo de LiteLLM](https://docs.litellm.ai/docs/proxy/cost_tracking)

Para importar otra exportación, prepará un JSONL normalizado con un objeto por llamada. `id` debe ser el identificador de la llamada en la fuente. `scope` identifica la conversación. `start` y `end` son horarios ISO 8601 con zona. `input` y `output` son los contadores nativos. Usá `null` para un contador faltante.

```json
{"scope":"qa-release-prueba","id":"id-de-la-fuente","start":"2026-11-19T12:00:00Z","end":"2026-11-19T12:00:01Z","input":120,"output":15,"model":"id-devuelto-por-el-proveedor"}
```

```sh
python3 v9/03-ejecuciones/scripts/qa.py tokens-check --run release-prueba --format native --file .trabajo/uso-agente.jsonl --scope qa-release-prueba
```

El campo `model` es opcional en QA V9 y se exige para [comparar modelos](scripts/benchmark/README.md). Copiá el modelo devuelto para esa llamada. En OpenTelemetry se lee `gen_ai.response.model`.

## Etapas y cierre

Marcá los cambios de etapa con `tokens-stage`. Las etapas son `preparacion`, `analisis`, `diseno`, `ejecucion` y `cierre`. Una llamada que cruza un cambio de etapa aparece como mixta. El consumo de la aplicación se documenta por separado.

`publish --zip` vuelve a leer la fuente y guarda el total observado, el corte y el detalle por llamada en el paquete. El detalle incluye un hash del identificador, horarios y contadores. Los archivos originales de telemetría quedan en el área de trabajo. El cierre queda pendiente si faltan contadores, desaparecieron llamadas de la comprobación inicial o el exportador todavía no cubrió el último intento. Si la conversación sigue activa, pueden aparecer más llamadas al finalizar el turno. Podés publicar una revisión con `--name` cuando se hayan exportado.

Para las corridas activas antes de incorporar esta verificación, conservá los informes originales. La recuperación de su consumo depende de que exista una fuente que permita atribuir cada llamada a esa corrida.
