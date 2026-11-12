# QA agentizada · V4

V4 prepara una sesión trazable para un agente de QA: indexa el segundo cerebro local, recupera pasajes con límites visibles y genera `log.md` a partir de eventos. El agente interpreta el contexto y propone casos. Con un perfil, el CLI ejecuta aserciones HTTP y pruebas de navegador con Playwright instalado. Las interacciones avanzadas y las consultas MCP se ejecutan desde el agente anfitrión.

## Cuarta iteración

Usá [el flujo con perfil](docs/ITERACION-4.md) para APIs, Swagger con Playwright y evidencia de bases de datos mediante MCP. El esquema nuevo registra resultados por criterio, tiempos observados y un CSV de requisitos. El esquema anterior sigue disponible para las sesiones existentes.

El [piloto local de PappU](docs/PILOTO-PAPPU.md) incluye los comandos, el alcance y los resultados observados.

## Estructura

- `src/qa.py`: interfaz de línea de comandos y operaciones del motor.
- `src/session.py`: persistencia y generación de la bitácora.
- `src/records.py`: validación de casos, intentos y hallazgos.
- `src/engine/`: motor documental basado en V2; `brain.py` procesa consultas, `document_utils.py` indexa documentos y `cli.py` expone los comandos. V3 reutiliza el índice de nombres entre documentos y procesa consultas en una sola pasada; conserva la CLI y el contrato de búsqueda.
- `docs/`: instrucciones de operación y contrato de registros.
- `examples/`: consultas y registros de ejemplo, sin resultados reales.
- `tests/`: verificaciones de V4.
- `tools/`: medición reproducible del motor; ver [rendimiento](docs/RENDIMIENTO.md). Las evidencias y pruebas históricas se conservan en `../historico/Post Harness V2/`.

Python 3.10+ y biblioteca estándar en Linux o macOS. El corpus debe ser un **directorio** de archivos textuales accesibles, no una base SQLite preexistente. Cada sesión y su SQLite deben ubicarse fuera del corpus y no compartirse entre escritores concurrentes. El motor comprueba la revisión del corpus; si cambia, crear una sesión nueva e indexar otra vez.

## Prompt para ejecutar la iteración

Abrí [PROMPT-MAESTRO.md](PROMPT-MAESTRO.md), completá las variables y pegalo en Copilot. No es obligatorio ubicarse en `v4`: el prompt usa la ruta absoluta del script. La [guía de medición](docs/MEDICION-TOKENS.md) define cómo registrar consumo por etapa cuando el entorno lo exponga. La sesión genera `casos.csv` con el plan y último estado, y `ejecuciones.csv` con todos los intentos. Ambos se regeneran desde los eventos; no editarlos manualmente.

## Inicio en el servidor

Desde un checkout de la rama `v4`, entrá a la carpeta `v4/`. Prepará un perfil JSON del entorno de QA usando [el ejemplo](examples/perfil-iteracion4.json). Adaptá el origen, las rutas y los controles a tu aplicación. Para ejecutar Playwright, instalá el paquete y Chromium en el mismo entorno Python. En Linux, consultá la [instalación oficial de dependencias de navegador](https://playwright.dev/python/docs/browsers#install-system-dependencies). El MCP de PostgreSQL, si se usa, tiene su propio [paso de instalación](../tools/postgres-mcp/README.md).

```sh
cd v4
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-playwright.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python -m unittest discover -s tests -q
```

Los casos HTTP y la auditoría también se pueden ejecutar con Python estándar sin Playwright. Creá una sesión nueva con `--profile` para activar el contrato V4. Usá el perfil real del servidor, no el perfil local de PAPPU. Si vas a leer el segundo cerebro, pasá el directorio textual como `--corpus`.

```sh
RUN=/ruta/qa-work/release-v4
.venv/bin/python src/qa.py init --run "$RUN" --profile /ruta/perfil-qa.json --corpus /ruta/segundo-cerebro --title 'QA release'
.venv/bin/python src/qa.py preflight --run "$RUN"
.venv/bin/python src/qa.py index --run "$RUN"
.venv/bin/python src/qa.py pack --run "$RUN" --queries /ruta/consultas.json
```

El agente debe adaptar las preguntas al alcance real, leer los JSON de `artifacts/`, ampliar el contexto cuando sea necesario y seguir [el protocolo de ejecución](docs/PROTOCOLO-AGENTE.md). La sesión guarda `run.json`, `events.json`, `brain.sqlite`, `session.json`, `artifacts/`, `log.md`, `casos.csv` y `ejecuciones.csv`. El log se regenera en cada operación; no editarlo directamente. Puede contener rutas, resultados y datos sensibles: revisar antes de compartirlo.

```sh
.venv/bin/python src/qa.py record --run "$RUN" --json /ruta/casos.json
.venv/bin/python src/qa.py freeze-plan --run "$RUN"
.venv/bin/python src/qa.py suite --run "$RUN" --manifest /ruta/suite.json
.venv/bin/python src/qa.py report --run "$RUN"
.venv/bin/python src/qa.py audit --run "$RUN"
```

Usá los [casos de ejemplo V4](examples/casos-iteracion4.json) como plantilla. Cada ejecución se vincula a un caso registrado y conserva el historial por criterio. El resumen muestra el último estado por caso. Para recorridos variables de UI y pruebas negativas de contrato, consultá [las pruebas exploratorias](docs/PRUEBAS-EXPLORATORIAS.md).

La CLI también ofrece `show`, `headings`, `links` y `verify`, y registra sus resultados en la bitácora: consultar `python3 src/qa.py --help`, `python3 src/engine/brain.py --help` y [la guía del motor](docs/MOTOR.md). Por ejemplo, `python3 src/qa.py show --run /ruta/qa-work/release-v4 "ruta/nota.md" --start 1 --end 80`. Las operaciones directas del motor y herramientas externas necesitan una nota explícita; no pegar credenciales ni contenido sensible. `verify` revisa estructura y rangos, no el respaldo semántico. El adaptador remoto RAGFlow de V2 no está integrado en esta CLI: esta V4 opera con un corpus local.

## Límites actuales

La V4 es un framework local, no una ejecución completa de QA de producto. La generación de casos y la ejecución de pruebas dependen del agente y de sus herramientas. Los registros ingresados con `record` y los resultados que acepta `verify` usan formatos distintos: `verify` no audita automáticamente los casos del log. Consultar [la guía del motor](docs/MOTOR.md) antes de usarlo. El log se reescribe completo tras cada operación; para lotes grandes conviene registrar una lista JSON. No se admite escritura concurrente en una sesión.
