# QA agentizada · V5

V5 es un harness autocontenido para que Copilot descubra el alcance de una aplicación, diseñe pruebas trazables, ejecute los casos factibles y publique una entrega portable a Obsidian. El prompt guía la selección de casos y herramientas a partir del objetivo, los contratos y las superficies que expone cada aplicación.

## Inicio

1. Copiá esta carpeta completa al servidor donde vayas a trabajar y abrila como workspace en Copilot.
2. Completá el [prompt maestro](PROMPT-MAESTRO.md) con el objetivo, entorno, alcance y accesos autorizados.
3. Copiá la subcarpeta de [resultados](resultados/) a Obsidian y compartí el HTML y las propuestas SDD con sus destinatarios.

El CLI requiere Python 3.10 o superior. HTTP y recuperación documental usan la biblioteca estándar. El runner de navegador requiere Playwright y Chromium o un canal compatible ya disponible. Instalá la dependencia opcional con `python3 -m pip install -r requirements-playwright.txt` en el entorno de QA. Los casos complejos se registran desde las herramientas autorizadas de Copilot. MCP es opcional y puede usarse como fuente de lectura si ya está conectado.

## Operación

Desde `v5/`, corré `python3 src/qa.py --help`. Cada comando con `--run` recibe un ID, por ejemplo `release-prueba`. El CLI crea la carpeta `.trabajo/<id>/`, que contiene los registros internos, las plantillas de texto y las evidencias de trabajo. Usá un solo escritor por corrida.

```sh
python3 src/qa.py init --run release-prueba --title "QA de release" --environment QA --version "build-42"
python3 src/qa.py preflight --run release-prueba
# Registrar casos con record y preparar el catálogo independiente si existe.
python3 src/qa.py freeze-plan --run release-prueba
# Ejecutar o registrar los intentos y completar las tres notas internas.
python3 src/qa.py publish --run release-prueba
python3 src/qa.py export-html --run release-prueba
python3 src/qa.py export-fixes --run release-prueba
```

- Pasá `--profile` con el perfil del entorno para declarar sondas HTTP, rutas, actores o fuentes MCP. `preflight` comprueba las sondas declaradas, presencia de variables y del paquete Playwright. El agente verifica las herramientas, los accesos y las dependencias pertinentes para el alcance.
- Pasá `--corpus` a `init` para un directorio textual. Usá `index`, luego `pack --queries ARCHIVO` con una lista JSON de preguntas. `show`, `headings` y `links` amplían el material. El CLI devuelve la ruta del artefacto interno que hay que leer. Si cambia la revisión del corpus, creá una corrida nueva.
- Usá `record --json ARCHIVO` o `record` con JSON por entrada estándar para casos, intentos, hallazgos y notas. El plan previo a la ejecución se conserva con `freeze-plan`. Si existe un alcance numerado independiente, pasá `--requirements CATALOGO` al congelarlo.
- Usá `execute --case ID --via http` o `--via playwright` para registrar una ejecución declarativa. `suite --manifest ARCHIVO` ejecuta un lote. Ver [contratos de registro y ejemplos](REGISTROS.md).
- Completá `analisis.md`, `metricas.md` y `evaluacion.md` en la carpeta interna antes de publicar. Citá las notas de evidencia mediante rutas relativas a la raíz de la entrega.

## Entrega

`publish` genera los siete Markdown en `resultados/<id>/` y copia las notas Markdown de evidencia referenciadas. Conserva plan inicial, casos vigentes, intentos, hallazgos y conteos del primer y último estado. Un fallo funcional aparece en el informe. El código de publicación indica si hubo problemas estructurales de evidencia, no si el producto aprobó. Una publicación anterior se conserva. Usá `--name <id-revision>` si hace falta exportar una versión corregida.

La revisión comprueba que la evidencia compartible exista y esté enlazada. La pertinencia, exactitud y sanitización requieren revisión del agente. El alcance, los efectos autorizados y el dictamen dependen de la aplicación y del usuario. Los resultados quedan ignorados por Git y disponibles como archivos locales.

## Reporte gerencial y propuestas SDD

- `export-html` guarda `reportes/<id>.html`. El reporte abre localmente y registra qué se probó, por qué se incluyó cada caso y qué se observó. Los intentos y criterios se pueden desplegar. Usá la nota `resumen-gerencial` para agregar contexto breve.
- `export-fixes` guarda un Markdown por defecto de producto confirmado y abierto en [SDD fixes](SDD%20fixes/). El campo `sdd` del hallazgo aporta el cambio sugerido, referencias y criterios de aceptación. Los hallazgos anteriores sin esos datos se exportan como borradores si su evidencia sigue disponible.
- Las [plantillas](templates/) se usan para construir el HTML, las propuestas SDD, el informe Markdown y el CSV. Para reexportar alguno de los archivos con cambios, indicá `--name <id-revision>`.

## CSV para Azure Test Plans

Desde `v5/`, generá el archivo con la ruta de área real del proyecto.

```sh
python3 src/qa.py export-azure --run release-prueba --area 'Proyecto\Área QA'
```

El CSV queda en `azure/release-prueba.csv`. Contiene una fila por paso y repite los datos del caso en cada fila. Cuando hay precondiciones, se exportan como primer paso. Cada acción toma su propio resultado esperado de `step_expected`. En casos anteriores al cambio, el esperado general se conserva en el último paso. Se mantienen los títulos originales y se deja el ID de Azure vacío para la creación de casos nuevos.

El estado predeterminado es `Design`. Usá `--assigned-to` con una identidad válida si el proyecto requiere asignación y `--state` si usa otro estado inicial. Usá `--name` para generar una revisión. El CSV incorpora los campos `Tipo de caso de prueba`, `Funcionalidad`, `Tipo de componente` y `Tipo`. Revisá el mapeo de esos cuatro campos en el asistente de Azure según la configuración del proyecto. La importación se realiza desde Azure Test Plans. [Formato y mapeo de importación de Microsoft](https://learn.microsoft.com/en-us/azure/devops/test/bulk-import-export-test-cases?view=azure-devops)

## Verificación del harness

```sh
python3 -m unittest discover -s tests -v
```

Para incluir el smoke real de navegador, ejecutá las pruebas con `QA_V5_TEST_BROWSER=chrome` o con otro canal disponible en ese equipo.
