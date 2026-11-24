# QA agentizada V8

Tres etapas con entregas en disco. QA fija los recorridos y su superficie en el encargo inicial. El agente usa el segundo cerebro para fundamentar esperados y diseñar casos. Python recupera las fuentes, arma el CSV, valida la suite y ejecuta las pruebas. Se puede repetir la tercera etapa con el catálogo ya preparado.

| Etapa | Entrada | Entrega | Instrucciones |
|---|---|---|---|
| 1. Análisis | Encargo y carpeta del segundo cerebro | Reglas y dudas por recorrido, revisión del corpus y extractos con referencias originales | [Prompt de análisis](01-analisis/PROMPT.md) |
| 2. Casos | Entrega de análisis, diseño de QA y documentación funcional opcional | CSV obligatorio, suite, perfil, pasos, criterios, datos, fuentes y pendientes | [Prompt de casos](02-casos/PROMPT.md) |
| 3. Ejecuciones | Carpeta de la segunda etapa y acceso al entorno autorizado | Dictamen, preflight y, cuando se ejecuta la suite, resultados por intento, evidencia, HTML, JUnit y ZIP | [Prompt de ejecución](03-ejecuciones/PROMPT.md) |

Cada etapa tiene su código en `scripts/` y sus registros en `logs/`. Las rutas comunes se resuelven desde el archivo del script, lo que permite mover el paquete completo. El inventario indica qué ejecutar, qué módulos usa cada comando y dónde están las herramientas de las iteraciones anteriores. [Inventario de scripts](INVENTARIO-SCRIPTS.md)

## Preparar el servidor

Descomprimí el ZIP y trabajá desde el directorio que contiene `v8/`. La distribución contiene el código Python de las tres etapas. Instalá las dependencias en el intérprete que usará QA (Python 3.10 o posterior).

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r v8/requirements.txt
```

En PowerShell se activa con `.\.venv\Scripts\Activate.ps1`. Para usar el perfil con Chromium administrado instalá el navegador con `python -m playwright install chromium`. En Linux puede requerir las dependencias del sistema. El perfil de la demo solicita Chrome instalado y lo usa sin ventana. Para PostgreSQL, ejecutá `python -m pip install -r v8/03-ejecuciones/requirements-postgres.txt`. El proceso del ejecutor necesita conectividad a la aplicación, sus actores de QA y los datos sintéticos del diseño.

## Probar las tres etapas

La demo usa el chatbot sintético incluido en el paquete. Ejecutá los comandos desde la raíz en el entorno preparado. Las rutas son argumentos explícitos, así se pueden mover las entregas completas entre máquinas.

```sh
python v8/01-analisis/scripts/analizar.py procesar --id demo-analisis --encargo v8/01-analisis/ejemplos/encargo.demo.json --corpus v8/01-analisis/ejemplos/corpus --revision v8/01-analisis/ejemplos/revision.demo.json
python v8/02-casos/scripts/preparar.py procesar --id demo-casos --analisis v8/01-analisis/salidas/demo-analisis --diseno v8/02-casos/ejemplos/diseno.demo.json
```

En una segunda terminal arrancá la aplicación con `python v8/03-ejecuciones/scripts/demo_chatbot.py`. Con el servidor en marcha, ejecutá el tercer comando.

```sh
python v8/03-ejecuciones/scripts/ejecutar.py procesar --id demo-ejecucion --casos v8/02-casos/salidas/demo-casos
```

El resultado esperado es un caso UI aprobado. Para comprobar la detección, detené el servidor de demo y levantalo con `--regression`. Repetí el tercer comando con `--id demo-regresion --build demo-con-falla`. El estado visible cambia y el caso debe fallar con la misma suite.

## Usar una release real

Abrí una conversación por etapa y completá el bloque de datos de su prompt. Desde la raíz del paquete, usá el mismo intérprete para los comandos. Cada pase se identifica por los archivos de la tabla.

| Carpeta generada | Archivo que la identifica | Quién la recibe |
|---|---|---|
| Recuperación inicial | `analisis.json` y extractos | Análisis, con `--base`, para cerrar las reglas |
| Análisis cerrado | `reglas.json` | El diseñador de casos, con `--analisis` |
| Consulta funcional opcional | `documentacion-funcional.json` | El diseñador de casos, con `--contexto-funcional` |
| Diseño publicado | `suite.json` y `casos-qa.csv` | El ejecutor, con `--casos` |
| Ejecución | `dictamen.json` | QA, para revisar cada recorrido y abrir su evidencia |

**Documentación funcional.** En `DOCUMENTACION_FUNCIONAL` del segundo prompt, QA puede adjuntar manuales, especificaciones o historias con criterios de aceptación. El diseño cita el documento original y el rango utilizado. Los archivos admitidos son Markdown, TXT y RST en UTF-8, texto y tablas de Word DOCX y PDF con texto extraíble (opcional: `python -m pip install pypdf`). Para un escaneo se puede aportar una transcripción. [Ejemplo de guía funcional](02-casos/ejemplos/guia-funcional.demo.md)

**Dictamen.** El preflight comprueba el arranque del navegador y las variables declaradas para los formularios. Un bloqueo previo queda registrado con cero intentos. La aplicación, los permisos y los esperados se verifican durante la ejecución. En `dictamen.json`, `cobertura_por_recorrido` vincula cada tarea del encargo con estado, casos y evidencia. El HTML de detalle está en `resultados/reporte gerencial.html`.

### Entrega CSV de QA

`02-casos/salidas/ID/casos-qa.csv` usa los diez campos de caso y los tres de paso del Markdown de QA, con sus rótulos en español. Una fila por paso, campos de caso repetidos, numeración desde 1, coma como separador, UTF-8 con BOM y comillas para celdas con comas o saltos de línea. Con precondiciones se crea el paso 1 y su esperado queda vacío. Sin precondiciones la primera acción es el paso 1. Un ID externo o asignado ausente queda vacío. Los nombres y valores del ejemplo de negocio son datos ilustrativos. Este archivo está destinado a QA. El comando avanzado de exportación a Azure Test Plans usa su propia plantilla y sus encabezados de importación.

### Logs, consumos y repetición

Los comandos principales escriben `logs/ID/INTENTO/resumen.json` en su propia carpeta, también ante errores de datos. Registra hora UTC, duración del script, salida, estado y huellas de las entradas o entregas. La primera etapa conserva estadísticas del índice; la segunda cuenta casos y filas; la tercera registra el navegador, el log del runner y sus eventos. Las entregas completas aparecen en `salidas/ID/` con un inventario SHA-256. Usá un ID nuevo para cada repetición. Los logs, resultados, perfiles reales y exportaciones con datos del piloto deben mantenerse en almacenamiento privado.

Los comandos principales de las tres etapas hacen **cero llamadas a modelos**. Para diseñar o interpretar resultados el agente sí puede consumir tokens. Usá una conversación exclusiva por etapa y exportación nativa sin contenido. Los extractos tienen un presupuesto configurable de caracteres; las búsquedas se procesan en lote. Para registrar el consumo observado al cierre de una conversación podés usar el subcomando `medir` de la etapa correspondiente.

```sh
python v8/02-casos/scripts/preparar.py medir --id demo-casos --archivo /ruta/otel.jsonl --scope ID_CONVERSACION --formato otel
```

También se admite `--formato native` con el [formato por llamada](03-ejecuciones/MEDICION-TOKENS.md). Cada corte conserva el hash del archivo, la conversación anonimizada, las llamadas únicas y los subtotales de entrada y salida disponibles. Usá el último corte de cada conversación. Si reintentás la misma etapa dentro de ese chat, registrá una sola vez el consumo acumulado de esos intentos. Sin exportación queda «sin medición». El tiempo del script y el consumo de modelos del producto bajo prueba se interpretan por separado.

Los códigos de salida son **0** para una operación satisfactoria, **1** para una suite rechazada, **2** para una entrada o ejecución inválida y **3** para un estado inconcluso. Un borrador de extracción se identifica en el log y necesita `reglas.json` para pasar a diseño. Una etapa con pendientes puede entregar sus materiales válidos y devolver 3. El resumen distingue trabajo bloqueado de fallos observados.

Para verificar los contratos entre etapas en un checkout de este proyecto, ejecutá `python -m unittest discover -s v8/03-ejecuciones/scripts -v` desde la raíz.

Para regenerar el ZIP desde el repositorio, ejecutá `python tools/empaquetar_v8.py`. Distribuye los scripts, prompts y ejemplos de V8 con el motor organizado por etapa. Las corridas locales quedan en sus carpetas de trabajo.
