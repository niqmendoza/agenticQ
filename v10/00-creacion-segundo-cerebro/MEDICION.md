# Medición de la creación del segundo cerebro

Usá una conversación exclusiva para la etapa 00 y un prefijo nuevo para todos los IDs de esa corrida, por ejemplo `piloto-qa17`. Anotá el commit y conservá las mismas consultas de QA, el presupuesto y el modelo al comparar corridas.

## 1. Activar la telemetría antes de abrir Copilot

Para Copilot CLI, configurá un exportador local por corrida antes de abrir la conversación. Guardá el archivo fuera del repositorio de la aplicación y del paquete de QA. [Exportador de GitHub Copilot CLI](https://docs.github.com/en/copilot/reference/enterprise-administrators/opentelemetry-reference#otel-environment-variables)

```sh
umask 077
QA_COPILOT_LOG_DIR="$(mktemp -d)"
export COPILOT_OTEL_FILE_EXPORTER_PATH="$QA_COPILOT_LOG_DIR/copilot-00.jsonl"
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT=NO_CONTENT
copilot
```

Para Copilot Chat en VS Code, usá la exportación a archivo que corresponda al tipo de sesión. En el exportador local de la extensión, configurá `github.copilot.chat.otel.enabled`, `github.copilot.chat.otel.exporterType` como `file` y `github.copilot.chat.otel.outfile` con la ruta absoluta. Mantené deshabilitada la captura de contenido. Para Agent Host aplicá la configuración correspondiente de tu organización. [Opciones de telemetría en VS Code](https://code.visualstudio.com/docs/agents/guides/monitoring-agents#enable-otel-monitoring)

## 2. Importar el corte después de publicar

Cuando la conversación haya terminado y el exportador haya escrito el último turno, ejecutá desde otra terminal el importador sobre el ID de publicación.

```sh
python v10/00-creacion-segundo-cerebro/scripts/publicar.py medir --id piloto-qa17-publicar --archivo "RUTA_PRIVADA/copilot-00.jsonl"
```

Si la fuente contiene varias conversaciones, sumá `--scope` con el ID nativo de la conversación de QA. Para contadores normalizados de un proveedor, usá `--formato native`. El corte guarda hashes de la conversación y la fuente, timestamps, llamadas únicas y contadores por modelo. Registrá un corte nuevo si la conversación sigue trabajando. El diagnóstico toma el último corte de cada conversación incluida, aunque existan varios IDs con cortes de la misma sesión. [Formato nativo por llamada](../03-ejecuciones/MEDICION-TOKENS.md#usar-una-exportación-nativa-del-proveedor)

Los tokens ausentes quedan en `null`. Las cifras de caracteres corresponden al contexto y al corpus publicados por los scripts. Los tokens corresponden a las llamadas atribuibles a la conversación en la fuente nativa.

## 3. Comprobar el pase a la etapa 01

Ejecutá el diagnóstico después de importar el corte. `--corrida` reúne los IDs que comparten el prefijo. Para recuperar una actividad anterior o con otro nombre, agregá `--actividad ID`. Se adjunta el ID de la entrega que estás diagnosticando.

```sh
python v10/00-creacion-segundo-cerebro/scripts/diagnosticar.py procesar --id piloto-qa17-diagnostico --corrida piloto-qa17 --cerebro v10/00-creacion-segundo-cerebro/salidas/piloto-qa17-publicar
```

Para medir la recuperación de requisitos concretos, prepará un JSON con preguntas acordadas por QA y pasalo con `--pruebas RUTA`. El campo `concepto` es `modulo/id` y `localizador` es opcional. Usá `--max-chars` si el análisis de QA trabaja con un presupuesto diferente del predeterminado de 16.000 caracteres.

```json
[
  {
    "id": "consulta-tramite",
    "consulta": "¿Qué estado informa la consulta del trámite QA-17?",
    "concepto": "api/consulta-estado",
    "localizador": "está en revisión"
  }
]
```

Sin ese archivo, el diagnóstico usa hasta seis sondas por título en áreas temáticas distintas. Las entregas anteriores usan los módulos. Estas sondas comprueban acceso al contenido publicado. Las consultas de QA permiten medir recuperación frente a requisitos elegidos de antemano.

El informe registra estructura OKF, rutas desde el índice, citas, cobertura por módulo, pendientes y recuperación con el motor de la etapa 01. Prueba cada consulta por separado y después junto con las demás bajo el mismo presupuesto. Eso permite ver si un concepto falta, si la búsqueda no lo trae o si se recupera individualmente y queda fuera del lote. El código de salida 3 indica un diagnóstico con hallazgos de estructura o recuperación. El estado del corte nativo queda registrado aparte.

## 4. Compartir resultados y comparar

- Enviá `salidas/ID-diagnostico/diagnostico.json` y `diagnostico.md`, o el `logs/ID-diagnostico/log00.md` que los reúne. El diagnóstico incluye métricas de búsquedas vacías, contexto publicado, recortes y repeticiones sin copiar los fragmentos de código ni el archivo original de telemetría.
- Para medir repetibilidad, publicá de nuevo con el mismo commit, configuración y fichas y compará `corpus_sha256`. Para medir el ahorro de tokens, compará dos corridas con el mismo alcance y modelo, y mirá también cuántas consultas de QA recuperaron los conceptos esperados y cuántos módulos quedaron documentados.
