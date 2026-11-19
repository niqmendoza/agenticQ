# Agentic QC V6

El analista usa el agente para descubrir casos y confirmar los resultados esperados con negocio. El catálogo aprobado se guarda con el producto. Cada release ejecuta ese catálogo con un comando y genera su propio dictamen y evidencia. El [prompt maestro](PROMPT-MAESTRO.md) cubre la ejecución de suites aprobadas, la exploración con documentación de la aplicación y la comparación con V5.

| Carpeta o archivo | Para qué sirve |
| --- | --- |
| [Prompt maestro](PROMPT-MAESTRO.md) y [guía de registros](REGISTROS.md) | Encargo para Copilot y formato de casos, intentos y hallazgos. |
| [docs/](docs/) | [Propuesta para gerencia](docs/Propuesta-Agentic-QC-V6.html) y [análisis técnico de V5](docs/Analisis-V5-framework-QA.md) que fundamenta V6. |
| [examples/](examples/) | Catálogos de demostración para el chatbot y la API de PappU. |
| [src/](src/), [tests/](tests/) y [templates/](templates/) | Implementación, pruebas automatizadas y plantillas de entrega. |
| [evaluate-llm/](evaluate-llm/) | Comparación de modelos con revisión independiente. |
| [azure-pipelines.yml](azure-pipelines.yml) | Plantilla de ejecución en CI y publicación de resultados. |

El repositorio versiona el código, las guías y los ejemplos. Las sesiones, resultados del piloto, entornos virtuales y paquetes generados quedan en las carpetas locales que Git ignora.

## Instalar en el equipo del analista

Desde la carpeta `v6`, con Python 3.10 o posterior, creá un entorno e instalá el paquete. En PowerShell activá el entorno con `.\.venv\Scripts\Activate.ps1`. En macOS y Linux usá `source .venv/bin/activate`.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install ".[api]"
python -m playwright install chromium
qc --help
```

Para PostgreSQL instalá también el extra `postgres`. Para pruebas exclusivamente de API alcanza con el extra `api`. La instalación de Chromium habilita las pruebas de pantalla. El CLI instalado guarda cada job en `.agentic-qc/` del directorio actual. `QC_WORKSPACE` elige otra raíz. Al invocar directamente `python src/qa.py`, la raíz predeterminada es la carpeta V6. Usá la misma raíz para operar sobre una corrida.

## Probar el flujo completo en una computadora

La demo incluye un chatbot local de trámites con datos sintéticos y respuestas fijas. Desde `v6/`, en una terminal:

```sh
python examples/chatbot/demo.py
```

En una segunda terminal con el entorno activo:

```sh
qc validate --suite examples/chatbot/suite.json
qc run --suite examples/chatbot/suite.json --env local --build demo-sano --id sano
```

La suite comprueba que la persona vea el estado y la fuente en la pantalla, que el servicio devuelva el dato según el esquema OpenAPI y que responda adecuadamente para un trámite inexistente. Para probar la detección, cerrá el servidor de demo con Ctrl+C, reinicialo con `python examples/chatbot/demo.py --regression` y ejecutá la misma suite con `--build demo-con-falla --id con-falla`. El dato cambia a «cerrado», fallan la pantalla y el servicio y sigue aprobando la consulta del trámite inexistente.

La entrega está en `.agentic-qc/resultados/<id>/` y su ZIP contiguo. `resultado.json` contiene el dictamen, casos, intentos y huellas. `junit.xml` sirve para CI. `reportes/<id>.html` y los Markdown describen lo observado. Un directorio por ID impide que un reintento pise la corrida anterior.

## Probar tu chatbot y comparar la corrida V5

1. **Para probar ya una aplicación propia**, abrí V6 en el agente, completá el [encargo](PROMPT-MAESTRO.md) con el endpoint real, entorno, build, fuentes y mecanismos de acceso. Si partís del ejemplo, copiá su catálogo al repo de tu aplicación. Sustituí sus reglas, actores, URL, controles, contrato y fixtures por los de tu producto. Los nombres de variables de entorno van en el perfil. Cada equipo mantiene su catálogo.
2. **Para repetir los casos exactos de V5**, esperá que termine esa corrida. Si conservás la carpeta privada de trabajo y su manifiesto declarativo, copialos al equipo de QC y promovelos con el comando siguiente. La promoción conserva los IDs, definiciones y fixtures del manifiesto y enumera lo que quede fuera. Revisá el perfil y los datos antes de versionarlos. Los casos manuales o ejecutados por una herramienta externa requieren su propia implementación o un intento externo documentado.
3. **Validá y ejecutá** con el mismo build, datos y entorno. Para conservar el contrato de la prueba, resolvé las fuentes citadas contra el corpus. Si V5 usó un localizador descriptivo que no existe literalmente, fijá una sección o rango de líneas verificable y registrá ese cambio. Podés usar `--profile` y `--corpus` para archivos del entorno.
4. **Compará las entregas.** El comparador admite el ZIP publicado de V5, la carpeta de notas y la carpeta de trabajo. El ZIP V5 permite recuperar veredictos por ID. Las definiciones ejecutables y las huellas comparables se obtienen con los eventos de la carpeta de trabajo.

```sh
qc promote --from-run /ruta/v5/.trabajo/corrida --manifest /ruta/al/manifiesto.json --app mi-chatbot --out qa-chatbot
qc validate --suite qa-chatbot/suite.json --corpus /ruta/al/segundo-cerebro
qc run --suite qa-chatbot/suite.json --corpus /ruta/al/segundo-cerebro --env QA --build BUILD_REAL --id contraste-v6
qc compare --baseline /ruta/al/resultado-v5.zip --candidate .agentic-qc/resultados/contraste-v6.zip --out comparacion-v5-v6.md
```

Los resultados se emparejan por ID y muestran primer y último estado e intentos. Cuando existen las huellas, el informe verifica si el diseño coincide. Los casos exclusivos, cambios de build y definiciones sin verificar aparecen por separado. Para comparar el esfuerzo de las personas, registrar el tiempo de preparación de ambas corridas desde el mismo punto de inicio.

## Qué versiona cada aplicación

| Archivo o carpeta | Contenido |
| --- | --- |
| `suite.json` | Identidad del producto, rutas de configuración, requisitos y contrato. El formato es `agentic-qc/suite-1`. |
| `casos.json` | ID estable, requisito, prioridad, precondiciones, esperado, fuente y criterios observables. Los casos pendientes permanecen en descubrimiento. |
| `pasos.json` | Selección ordenada y canal por caso. `depends_on` contiene IDs previos. Un bloqueo afecta a los casos que dependen de él. |
| `perfil.json` | Origen, operaciones, actores, variables, controles, tablas o vistas de lectura autorizadas. |
| `fixtures/`, `docs/` y OpenAPI | Datos sintéticos, fuentes localizables y contrato utilizado por la suite. Conservar la revisión del producto y del catálogo en Git. |

El [ejemplo del chatbot](examples/chatbot/suite.json) usa JSON y OpenAPI YAML. El [perfil de PappU](examples/pappu-api/suite.json) demuestra un segundo producto con dos consultas de salud documentadas. Para validarlo, pasá `--corpus /ruta/PAPU/docs/PappU`. Son casos de disponibilidad. Para validar un recorrido de negocio de PappU, agregá el escenario y sus reglas al catálogo.

Los canales son `playwright` para navegador, `api` para requests con Playwright sin navegador, `http` para el cliente de biblioteca estándar y `db` para SQLite/PostgreSQL de lectura. Las rutas efectivas se cotejan contra el perfil. `qc openapi --spec archivo.yaml` inventaría operaciones. La demo usa una respuesta JSON de OpenAPI 3.1, con referencias locales. Los esquemas recursivos y las referencias remotas requieren un contrato autocontenido compatible. Para afirmar un resultado concreto, acompañá el esquema con un criterio de negocio.

Para correlacionar datos entre canales, usá `{{RUN_ID}}` en el dato sintético, la ruta aprobada o el filtro de consulta. Un paso API puede declarar `"capture": {"registro": ["id"]}` en el manifiesto. En otro caso que dependa del primero, `{{registro}}` refiere al ID devuelto. Solo se admiten identificadores cortos alfanuméricos, con guion o guion bajo. Un paso final independiente puede limpiar por el ID sintético de corrida aun cuando falle una verificación. Declarar explícitamente su operación en el perfil. Cada intento de escritura se ejecuta una vez. Para un efecto asíncrono, un paso GET, HEAD o DB puede declarar `"poll": {"attempts": 3, "interval_seconds": 2}`. El informe conserva todos los intentos.

## Dictamen, defectos y Azure

El plan congelado define los casos obligatorios de la release. Un fallo observado en un caso obligatorio produce código **1**. Si faltan pruebas, requisitos o evidencia válida, produce **3**. Todos los casos obligatorios aprobados con evidencia válida producen **0**. Una entrada inválida devuelve **2**. Un fallo de comprobación requiere triage para confirmar si hay defecto del producto. El CLI de descubrimiento permite publicar un informe aunque la release haya fallado. Usá `qc gate --run ID` para obtener el dictamen de esa sesión.

Cuando falla un caso del catálogo, el ZIP incluye una ficha en `triage/` con reproducción y evidencia por criterio. Ante un defecto confirmado registrá un `finding` con `record`, según la [guía de campos](REGISTROS.md). `qc export-fixes --run ID` escribe una ficha Markdown con evidencia portable y, en una regresión de catálogo, el comando y la revisión de la suite. Repetí el catálogo sobre el build corregido y usá `qc verify-fix --run ORIGINAL --finding F-01 --retest CORREGIDA`. La transición exige otro build del mismo entorno y casos equivalentes aprobados con evidencia. Republicá con `--name` para conservar las dos revisiones.

La [plantilla de Azure Pipelines](azure-pipelines.yml) ejecuta el CLI, publica JUnit incluso cuando hay fallos y conserva el paquete de resultados. El agente del pipeline necesita conectividad al ambiente seleccionado y sus variables de acceso. En Test Plans se puede asociar un caso existente desde los resultados del pipeline. Para importar diseño por CSV, `qc export-azure --run ID --area 'Proyecto\QA'` conserva `azure.work_item_id` cuando está informado. QC mantiene el mapeo por aplicación. Un ID vacío indica un alta en Azure. [Asociación en Azure DevOps](https://learn.microsoft.com/en-us/azure/devops/test/associate-automated-test-with-test-case?view=azure-devops)

## Evaluar modelos

El [benchmark](evaluate-llm/README.md) registra consigna, modelo observado, tokens y calidad revisada por etapa. En este modo usá `init --benchmark`. El comando `qc-benchmark` ofrece el mismo evaluador desde el paquete instalado. Para comparar la detección de fallas conocidas, un revisor usa `qc score-models --experiment experimento.json --out calidad.md` con resultados de suites en builds sanos y con regresiones. El [ejemplo de experimento](evaluate-llm/experimento.ejemplo.json) describe el formato. La mediana y la proporción de corridas evaluables ayudan a interpretar la muestra. La identidad que declara este segundo archivo debe cotejarse con la telemetría del benchmark.

## Verificar el framework

Desde `v6/` ejecutá `python -m unittest discover -s tests -v`. Con Chrome instalado, `QA_V6_TEST_BROWSER=chrome python -m unittest discover -s tests -v` incluye la integración de navegador. El servidor de fixtures de las pruebas vive en un puerto local temporal.
