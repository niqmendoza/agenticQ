# QA agentizada · V3

V3 prepara una sesión trazable para un agente de QA: indexa el segundo cerebro local, recupera pasajes con límites visibles y genera `log.md` a partir de eventos. El agente interpreta el contexto, propone casos, ejecuta pruebas disponibles y registra resultados. **El script no llama por sí solo a un modelo ni a Playwright**; requiere un agente con acceso a esas herramientas y al entorno de prueba.

## Estructura

- `src/qa.py`: interfaz de línea de comandos y operaciones del motor.
- `src/session.py`: persistencia y generación de la bitácora.
- `src/records.py`: validación de casos, intentos y hallazgos.
- `src/engine/`: motor documental basado en V2; `brain.py` procesa consultas, `document_utils.py` indexa documentos y `cli.py` expone los comandos. V3 reutiliza el índice de nombres entre documentos y procesa consultas en una sola pasada; conserva la CLI y el contrato de búsqueda.
- `docs/`: instrucciones de operación y contrato de registros.
- `examples/`: consultas y registros de ejemplo, sin resultados reales.
- `tests/`: verificaciones de V3.
- `tools/`: medición reproducible del motor; ver [rendimiento](docs/RENDIMIENTO.md). Las evidencias y pruebas históricas se conservan en `../historico/Post Harness V2/`.

Python 3.10+ y biblioteca estándar en Linux o macOS. El corpus debe ser un **directorio** de archivos textuales accesibles, no una base SQLite preexistente. Cada sesión y su SQLite deben ubicarse fuera del corpus y no compartirse entre escritores concurrentes. El motor comprueba la revisión del corpus; si cambia, crear una sesión nueva e indexar otra vez.

## Prompt para ejecutar la iteración

Abrí [PROMPT-MAESTRO.md](PROMPT-MAESTRO.md), completá las variables y pegalo en Copilot. No es obligatorio ubicarse en `qa-v3`: el prompt usa la ruta absoluta del script. La [guía de medición](docs/MEDICION-TOKENS.md) define cómo registrar consumo por etapa cuando el entorno lo exponga. La sesión genera `casos.csv` con el plan y último estado, y `ejecuciones.csv` con todos los intentos. Ambos se regeneran desde los eventos; no editarlos manualmente.

## Inicio en el servidor

Copiá toda esta carpeta al servidor por el mecanismo habitual del equipo. Configurá las rutas de acuerdo con ese entorno. No copies secretos ni sesiones del piloto al repositorio. Desde la carpeta V3:

```sh
python3 src/qa.py init --run /ruta/qa-work/release-v3 --corpus /ruta/segundo-cerebro --title 'QA release'
python3 src/qa.py index --run /ruta/qa-work/release-v3
python3 src/qa.py pack --run /ruta/qa-work/release-v3 --queries examples/queries.json
```

El agente debe adaptar las preguntas al alcance real, leer los JSON de `artifacts/`, ampliar el contexto cuando sea necesario y seguir [el protocolo de ejecución](docs/PROTOCOLO-AGENTE.md). La sesión guarda `run.json`, `events.json`, `brain.sqlite`, `session.json`, `artifacts/`, `log.md`, `casos.csv` y `ejecuciones.csv`. El log se regenera en cada operación; no editarlo directamente. Puede contener rutas, resultados y datos sensibles: revisar antes de compartirlo.

```sh
python3 src/qa.py record --run /ruta/qa-work/release-v3 --json examples/case.json
python3 src/qa.py record --run /ruta/qa-work/release-v3 --json examples/execution.json
python3 src/qa.py record --run /ruta/qa-work/release-v3 --json examples/finding.json
python3 src/qa.py report --run /ruta/qa-work/release-v3
python3 -m unittest discover -s tests -v
```

Los ejemplos son sintéticos: no registrarlos en una sesión real. Consultá [registros y límites](docs/REGISTROS.md) para crear los propios. Cada ejecución debe referir a un caso ya registrado; los reintentos se preservan y el resumen cuenta el último estado por caso. El log es una bitácora, no una certificación de calidad ni un reporte de cobertura automatizado.

La CLI también ofrece `show`, `headings`, `links` y `verify`, y registra sus resultados en la bitácora: consultar `python3 src/qa.py --help`, `python3 src/engine/brain.py --help` y [la guía del motor](docs/MOTOR.md). Por ejemplo, `python3 src/qa.py show --run /ruta/qa-work/release-v3 "ruta/nota.md" --start 1 --end 80`. Las operaciones directas del motor y herramientas externas necesitan una nota explícita; no pegar credenciales ni contenido sensible. `verify` revisa estructura y rangos, no el respaldo semántico. El adaptador remoto RAGFlow de V2 no está integrado en esta CLI: esta V3 opera con un corpus local.

## Límites actuales

La V3 es un prototipo local, no una ejecución completa de QA de producto. La generación de casos y la ejecución de pruebas dependen del agente y de sus herramientas. Los registros ingresados con `record` y los resultados que acepta `verify` usan formatos distintos: `verify` no audita automáticamente los casos del log. Consultar [la guía del motor](docs/MOTOR.md) antes de usarlo. El log se reescribe completo tras cada operación; para lotes grandes conviene registrar una lista JSON. No se admite escritura concurrente en una sesión.
