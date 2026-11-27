# QA agentizada V10

Cuatro etapas con entregas en disco. La etapa 00 publica un segundo cerebro OKF desde un commit local, con conceptos vinculados y citas al código. QA fija los recorridos y su superficie en el encargo de análisis. El agente usa el corpus para fundamentar esperados y diseñar casos. Python recupera las fuentes, arma el CSV, valida la suite y ejecuta las pruebas. La etapa 03 se puede repetir con el catálogo ya preparado.

| Etapa | Entrada | Entrega | Instrucciones |
|---|---|---|---|
| 00. Creación del segundo cerebro | Repositorio Git local, commit y taxonomía de producto | Bundle OKF 0.2 con conceptos por temas, MOCs, relaciones justificadas y referencias al código | [Prompt de creación](00-creacion-segundo-cerebro/PROMPT.md) |
| 01. Análisis | Encargo y entrega de 00 o un corpus existente | Reglas y dudas por recorrido, revisión del corpus y extractos con referencias originales | [Prompt de análisis](01-analisis/PROMPT.md) |
| 02. Casos | Entrega de análisis, diseño de QA y documentación funcional opcional | CSV obligatorio, suite, perfil, pasos, criterios, datos, fuentes y pendientes | [Prompt de casos](02-casos/PROMPT.md) |
| 03. Ejecuciones | Entrega de casos y acceso al entorno autorizado | Dictamen, preflight y, cuando se ejecuta la suite, resultados por intento, evidencia, HTML, JUnit y ZIP | [Prompt de ejecución](03-ejecuciones/PROMPT.md) |

[Tabla de cambios y beneficios](MEJORAS-V10.md)

Cada etapa tiene su código en `scripts/` y sus registros en `logs/`. Las rutas comunes se resuelven desde el archivo del script, lo que permite mover el paquete completo. El inventario indica qué ejecutar, qué módulos usa cada comando y dónde están las herramientas de las iteraciones anteriores. [Inventario de scripts](INVENTARIO-SCRIPTS.md)

## Preparar el servidor

Descomprimí el ZIP y trabajá desde el directorio que contiene `v10/`. La distribución contiene el código Python de las cuatro etapas. La etapa 00 usa Python 3.10 o posterior y Git local. Instalá las dependencias de ejecución en el intérprete que usará QA.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r v10/requirements.txt
```

En PowerShell se activa con `.\.venv\Scripts\Activate.ps1`. Para usar el perfil con Chromium administrado instalá el navegador con `python -m playwright install chromium`. En Linux puede requerir las dependencias del sistema. El perfil de la demo solicita Chrome instalado y lo usa sin ventana. Para PostgreSQL, ejecutá `python -m pip install -r v10/03-ejecuciones/requirements-postgres.txt`. El proceso del ejecutor necesita conectividad a la aplicación, sus actores de QA y los datos sintéticos del diseño.

### Credenciales de la VM

El ZIP instala un `v10/credenciales.txt` vacío de valores. En un checkout, copiá `credenciales.ejemplo.txt` como `credenciales.txt` con permisos privados. Completá solo las variables declaradas por los casos. En Linux o macOS, aplicá `chmod 600 v10/credenciales.txt` antes de guardar valores.

```sh
install -m 600 v10/credenciales.ejemplo.txt v10/credenciales.txt
```

El formato es `NOMBRE=valor` por línea. El valor es literal y las líneas que comienzan con `#` son comentarios. Si la variable ya está en el entorno, se usa ese valor. Para UI referenciá nombres en `value_env`, para API en `perfil.credentials` y para PostgreSQL en `dsn_env`. Podés pasar otra ruta con `--credenciales`. Guardá el archivo en la VM y compartí solo su ruta y los nombres requeridos. El empaquetador agrega el ejemplo vacío y excluye el archivo local. Para SSO o MFA, confirmá con QA qué modo de acceso está habilitado en el entorno y documentalo en el encargo.

## Crear o actualizar el segundo cerebro

`mapear.py` inventaría los archivos elegibles del commit, redacta patrones sensibles y crea borradores por módulo. `navegar.py` sirve a Copilot el mapa, búsquedas y rangos dentro de un presupuesto. Copilot redacta las afirmaciones y las vincula con fragmentos exactos. `publicar.py` valida las citas y arma el bundle OKF que recibe la etapa 01. [Formato del bundle](00-creacion-segundo-cerebro/FORMATO.md)

```sh
python v10/00-creacion-segundo-cerebro/scripts/mapear.py procesar --id mapa --repo "REPO_LOCAL" --app "APLICACION" --rev HEAD
python v10/00-creacion-segundo-cerebro/scripts/navegar.py procesar --id contexto-00 --mapa v10/00-creacion-segundo-cerebro/salidas/mapa --resumen
python v10/00-creacion-segundo-cerebro/scripts/publicar.py procesar --id cerebro --mapa v10/00-creacion-segundo-cerebro/salidas/mapa --taxonomia "TAXONOMIA.json" --revision "FICHA.json"
python v10/01-analisis/scripts/analizar.py procesar --id analisis --encargo "ENCARGO.json" --cerebro v10/00-creacion-segundo-cerebro/salidas/cerebro
```

Para actualizar una entrega, agregá `--anterior` a `mapear.py` y `publicar.py`. El mapa identifica los módulos que necesitan revisión, y la publicación puede conservar fichas respaldadas por el mismo código. Para migrar una aplicación que ya tiene su segundo cerebro, podés seguir usando `analizar.py --corpus`. [Formato, configuración y métricas](00-creacion-segundo-cerebro/FORMATO.md)

Para una corrida de medición, activá la telemetría de Copilot antes de empezar. `publicar.py medir` importa el corte y `diagnosticar.py` reúne el consumo, la navegación del repositorio y la recuperación del bundle con el motor de la etapa 01. [Medición y diagnóstico de la etapa 00](00-creacion-segundo-cerebro/MEDICION.md)

## Probar análisis, casos y ejecución

La demo usa el chatbot sintético incluido en el paquete. Ejecutá los comandos desde la raíz en el entorno preparado. Las rutas son argumentos explícitos, así se pueden mover las entregas completas entre máquinas.

```sh
python v10/01-analisis/scripts/analizar.py procesar --id demo-analisis --encargo v10/01-analisis/ejemplos/encargo.demo.json --corpus v10/01-analisis/ejemplos/corpus --revision v10/01-analisis/ejemplos/revision.demo.json
python v10/02-casos/scripts/preparar.py procesar --id demo-casos --analisis v10/01-analisis/salidas/demo-analisis --diseno v10/02-casos/ejemplos/diseno.demo.json
```

En una segunda terminal arrancá la aplicación con `python v10/03-ejecuciones/scripts/demo_chatbot.py`. Con el servidor en marcha, ejecutá el tercer comando.

```sh
python v10/03-ejecuciones/scripts/ejecutar.py procesar --id demo-ejecucion --casos v10/02-casos/salidas/demo-casos
```

El resultado esperado es un caso UI aprobado. Para comprobar la detección, detené el servidor de demo y levantalo con `--regression`. Repetí el tercer comando con `--id demo-regresion --build demo-con-falla`. El estado visible cambia y el caso debe fallar con la misma suite.

## Usar una release real

Abrí una conversación por etapa y completá el bloque de datos de su prompt. Cuando el corpus ya existe, arrancá en la etapa 01. Desde la raíz del paquete, usá el mismo intérprete para los comandos. Cada pase se identifica por los archivos de la tabla.

| Carpeta generada | Archivo que la identifica | Quién la recibe |
|---|---|---|
| Segundo cerebro publicado | `manifiesto.json` y `corpus/` | Análisis, con `--cerebro` |
| Recuperación inicial | `analisis.json` y extractos | Análisis, con `--base`, para cerrar las reglas |
| Análisis cerrado | `reglas.json` | El diseñador de casos, con `--analisis` |
| Consulta funcional opcional | `documentacion-funcional.json` | El diseñador de casos, con `--contexto-funcional` |
| Diseño publicado | `suite.json` y `casos-qa.csv` | El ejecutor, con `--casos` |
| Ejecución | `dictamen.json` | QA, para revisar cada recorrido y abrir su evidencia |

**Documentación funcional.** En `DOCUMENTACION_FUNCIONAL` del segundo prompt, QA puede adjuntar manuales, especificaciones o historias con criterios de aceptación. El diseño cita el documento original y el rango utilizado. Los archivos admitidos son Markdown, TXT y RST en UTF-8, texto y tablas de Word DOCX y PDF con texto extraíble (opcional: `python -m pip install pypdf`). Para un escaneo se puede aportar una transcripción. [Ejemplo de guía funcional](02-casos/ejemplos/guia-funcional.demo.md)

**Alcance.** El encargo declara `superficies` y cada recorrido tiene su propia superficie. Para una funcionalidad de UI y API, usá IDs distintos vinculados con `grupo`. `app` admite el nombre visible y el script deriva un `app_id` técnico.

**Fixtures.** `mockups.py` genera archivos JSON, CSV, TXT, Markdown, HTML, DOCX, XLSX y PDF a partir de la [especificación de ejemplo](02-casos/ejemplos/mockup.demo.json). Cada entrega conserva formato, semilla, huellas y estructura cuando corresponde. Agregá una o más entregas con `preparar.py --mockups RUTA`. El PDF sintético admite texto WinAnsi. Los recursos persistentes, sus permisos y su limpieza se definen en el entorno de QA.

**Preflight y dictamen.** La corrida comprueba el navegador, la conectividad TCP y los requisitos por caso. Para UI autenticada, `browser_setups` permite comprobar una vez por actor el login, el control listo y una sonda opcional, y reutilizar su estado en contextos separados. Los casos independientes siguen aunque otros se bloqueen. `--solo-preflight` ejecuta la comprobación sin casos y con sesiones descartables. Pasá `--build-ref` con la referencia del despliegue. `dictamen.json` publica cobertura, estados y evidencias. El HTML de detalle está en `resultados/reporte gerencial.html`. [Contrato Playwright](03-ejecuciones/PERFIL-PLAYWRIGHT.md)

**Fuentes.** El motor redacta patrones de secretos antes de indexar o extraer. Reindexá el corpus al pasar de V9 a V10. Revisá `indice.json` para conocer los archivos afectados. Si una cita no se puede verificar, `citas-invalidas.json` lista todas las causas detectadas y los rangos recuperados. La detección es heurística y los originales siguen siendo privados.

### Entrega CSV de QA

`02-casos/salidas/ID/casos-qa.csv` usa las 13 columnas del formato de QA en su orden exacto, una fila por paso, coma como separador, UTF-8 con BOM y fin de registro CRLF. Con precondiciones se crea el paso 1 y su esperado queda vacío. Sin precondiciones la primera acción es el paso 1. Un ID externo o asignado ausente queda vacío. Los valores por defecto del contrato son `test case`, `Design` y `Functional`. El diseño conserva los valores de clasificación que QA declara. `exportar_azure.py` fija columnas, valores y reglas de serialización para la importación actual de QA en Azure Test Plans. Actualizá ese archivo y el control de formato al cambiar el contrato.

```sh
python v10/02-casos/scripts/exportar_azure.py --casos "RUTA/casos.json" --area-qa "AREA_QA" --salida "casos-qa.csv"
```

El CSV de trabajo se publica como parte de la entrega de `preparar.py`. El comando directo permite regenerarlo como archivo nuevo para verificar el formato. La herramienta heredada `qa.py export-azure` conserva su plantilla avanzada.

### Logs, consumos y repetición

Cada ID genera un `logs/ID/log00.md`, `log01.md`, `log02.md` o `log03.md` según la etapa. Al cerrar, llamá `consolidar` sobre el script de esa etapa con todos los IDs de este encargo. El comando produce el Markdown único en la carpeta `logs/`. Incluye los archivos textuales publicados, diagnósticos, evidencia, resultados, cortes de consumo ya generados e inventario de binarios con tamaños y SHA-256. Las copias de texto idénticas remiten al anexo que ya las contiene.

```sh
python v10/03-ejecuciones/scripts/ejecutar.py consolidar --id QA-preflight --id QA-corrida --id QA-reintento
```

Los comandos principales escriben `logs/ID/INTENTO/resumen.json` en su propia carpeta, también ante errores de datos. Registra hora UTC, duración del script, salida, estado y huellas de las entradas o entregas. La primera etapa conserva estadísticas del índice; la segunda cuenta casos y filas; la tercera registra el navegador, el log del runner y sus eventos. Las entregas completas aparecen en `salidas/ID/` con un inventario SHA-256. Usá un ID nuevo para cada repetición. Los logs, resultados, perfiles reales y exportaciones con datos del piloto deben mantenerse en almacenamiento privado.

Los scripts de las cuatro etapas hacen **cero llamadas a modelos** en el flujo principal. Copilot puede consumir tokens al revisar el código, redactar fichas, diseñar casos e interpretar resultados. Usá una conversación exclusiva por etapa y exportación nativa sin contenido. Los extractos tienen un presupuesto configurable de caracteres y las búsquedas se procesan en lote. Para registrar el consumo observado al cierre de una conversación usá `medir`.

```sh
python v10/02-casos/scripts/preparar.py medir --id demo-casos --archivo /ruta/otel.jsonl --scope ID_CONVERSACION --formato otel
```

También se admite `--formato native` con el [formato por llamada](03-ejecuciones/MEDICION-TOKENS.md). Cada corte conserva el hash del archivo, la conversación anonimizada, las llamadas únicas y los subtotales de entrada y salida disponibles. Usá el último corte de cada conversación. Si reintentás la misma etapa dentro de ese chat, registrá una sola vez el consumo acumulado de esos intentos. Sin exportación queda «sin medición». El tiempo del script y el consumo de modelos del producto bajo prueba se interpretan por separado.

`metricas-etapa.json` resume cada ID. Distingue el tiempo de script de la ventana entre el primer inicio y el último fin registrado, que puede incluir pausas. En ejecución agrega espera observada en Playwright y reintentos de lectura, duración del preflight y causas. Conserva tokens de entrada y salida de los cortes nativos disponibles. Para comparar dos versiones usá alcance, entorno, builds y modelo equivalentes, y reportá intentos, casos sin intento y cobertura junto al tiempo y los tokens.

### Retest y decisión manual

Repetí la ejecución con un ID nuevo y mantené ambas carpetas completas. `historial_retest.py` compara sus entregas, identifica cambios de perfil o entradas por caso y adjunta las referencias a evidencia. Si QA documentó una decisión, pasá `--disposicion RUTA.json` con un objeto indexado por ID de caso.

```json
{
  "CHAT-UI": {
    "decision": "requiere_revision",
    "responsable": "Equipo QA",
    "motivo": "Se necesita contrastar el resultado con el entorno funcional",
    "evidencia": "QA-123"
  }
}
```

`decision` admite `aceptado`, `rechazado` y `requiere_revision`. El historial queda en `03-ejecuciones/logs/ID_ACTUAL/` y se incorpora a `log03.md`.

Los códigos de salida son **0** para una operación satisfactoria, **1** para una suite rechazada, **2** para una entrada o ejecución inválida y **3** para un estado inconcluso. Un borrador de extracción se identifica en el log y necesita `reglas.json` para pasar a diseño. Una etapa con pendientes puede entregar sus materiales válidos y devolver 3. El resumen distingue trabajo bloqueado de fallos observados.

Para verificar el pase desde creación del corpus, ejecutá `python -m unittest discover -s v10/00-creacion-segundo-cerebro/scripts -v`. Para análisis, diseño y ejecución usá `python -m unittest discover -s v10/03-ejecuciones/scripts -v`.

Para regenerar el ZIP, ejecutá `python v10/scripts/empaquetar_v10.py` desde el directorio que contiene `v10/`. Distribuye los scripts, prompts y ejemplos de V10 con el motor organizado por etapa. Las corridas locales quedan en sus carpetas de trabajo.
