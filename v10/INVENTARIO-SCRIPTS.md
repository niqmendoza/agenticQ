# Inventario de scripts de V10

V10 conserva los scripts y las herramientas avanzadas que quedaron agrupados en V8. La distribución incluye el motor dentro de `v10/`. Los adaptadores de RAGFlow y Ollama provienen del piloto Post Harness V2 y se ejecutan por separado.

## 00 · Creación del segundo cerebro

| Archivo | Uso |
|---|---|
| [mapear.py](00-creacion-segundo-cerebro/scripts/mapear.py) | Inventaría el commit, crea el índice redactado y prepara borradores por módulo. |
| [navegar.py](00-creacion-segundo-cerebro/scripts/navegar.py) | Devuelve mapas, búsquedas agrupadas y rangos con presupuesto sobre el JSON completo. |
| [publicar.py](00-creacion-segundo-cerebro/scripts/publicar.py), [tematico.py](00-creacion-segundo-cerebro/scripts/tematico.py), [okf.py](00-creacion-segundo-cerebro/scripts/okf.py) | Validan citas y relaciones, reutilizan fichas vigentes y escriben el grafo temático OKF 0.2. |
| [exportar_vault.py](00-creacion-segundo-cerebro/scripts/exportar_vault.py) | Copia el corpus a una bóveda nueva y enlaza notas preexistentes cuando se indican. |
| [diagnosticar.py](00-creacion-segundo-cerebro/scripts/diagnosticar.py), [evaluar_okf.py](00-creacion-segundo-cerebro/scripts/evaluar_okf.py) | Reúnen el consumo nativo y el contexto de la corrida, y verifican el bundle y su recuperación con el motor de 01. |
| [repositorio.py](00-creacion-segundo-cerebro/scripts/repositorio.py), [indice.py](00-creacion-segundo-cerebro/scripts/indice.py), [fichas.py](00-creacion-segundo-cerebro/scripts/fichas.py) | Leen Git, consultan SQLite y verifican el formato y las huellas de las fichas. |
| [test_cerebro.py](00-creacion-segundo-cerebro/scripts/test_cerebro.py) | Prueba el flujo sobre commits sintéticos, el presupuesto y el pase a 01. |

## 01 · Análisis del segundo cerebro

| Archivo | Uso |
|---|---|
| [alcance.py](01-analisis/scripts/alcance.py) | Normaliza nombres de aplicación y valida superficies, recorridos y prioridades. |
| [analizar.py](01-analisis/scripts/analizar.py) | Prepara el contexto a partir del encargo y cierra la revisión con citas al original. |
| [brain.py](01-analisis/scripts/brain.py) | CLI del motor documental. Indexa, recupera por consulta, navega por encabezados y vínculos, devuelve rangos y verifica referencias. |
| [cli.py](01-analisis/scripts/cli.py) | Implementa los comandos del motor, sus límites y logs. |
| [document_utils.py](01-analisis/scripts/document_utils.py) | Extrae texto y resuelve elementos de la estructura documental. |
| [ragflow/retrieve.py](01-analisis/scripts/ragflow/retrieve.py), [verify_context.py](01-analisis/scripts/ragflow/verify_context.py) | Recuperación opcional por API de RAGFlow y verificación de hashes, referencias y presupuesto del paquete. La recuperación con sesión requiere Linux o macOS. |
| [ragflow/context_packet.py](01-analisis/scripts/ragflow/context_packet.py), [ragflow_client.py](01-analisis/scripts/ragflow/ragflow_client.py) | Construyen el paquete de evidencia y consultan el servicio RAGFlow configurado. |

### Navegación puntual con el motor local

`analizar.py procesar` agrupa las consultas, indexa el corpus y recupera secciones bajo el presupuesto de caracteres. Agregá `--conservar-indice` al recuperar si querés usar la misma sesión para revisar encabezados, enlaces, rangos o nuevas consultas. El resumen del intento indica la ruta `navegacion`, que conserva el índice, la sesión y las llamadas del motor. Mantené esa carpeta en el área privada del corpus.

Desde la carpeta que contiene `v10/`, asigná a `NAV` la ruta indicada en el log. Usá en los comandos la ruta relativa al corpus que figure en `analisis.json`.

```sh
python v10/01-analisis/scripts/brain.py --db "$NAV/indice.sqlite" --session "$NAV/sesion.json" --log-dir "$NAV" headings reglas.md
python v10/01-analisis/scripts/brain.py --db "$NAV/indice.sqlite" --session "$NAV/sesion.json" --log-dir "$NAV" links reglas.md
python v10/01-analisis/scripts/brain.py --db "$NAV/indice.sqlite" --session "$NAV/sesion.json" --log-dir "$NAV" show reglas.md --start 1 --end 3 --max-chars 4000 --replay
```

`index` y `status` administran el índice. `pack` recibe un JSON con una lista de consultas y permite limitar documentos, líneas y caracteres. `verify` comprueba los rangos citados en un JSON contra el índice y la sesión que entregó esos fragmentos. Para incorporar al diseño una regla encontrada en una consulta puntual, ajustá la consulta del recorrido y generá una recuperación que incluya el fragmento citable.

## 02 · Diseño y CSV de QA

| Archivo | Uso |
|---|---|
| [mockups.py](02-casos/scripts/mockups.py), [formatos_fixture.py](02-casos/scripts/formatos_fixture.py) | Generan y comprueban fixtures JSON, CSV, TXT, Markdown, HTML, DOCX, XLSX y PDF con metadatos reproducibles. |
| [documentacion.py](02-casos/scripts/documentacion.py) | Recupera extractos de la documentación funcional opcional. |
| [preparar.py](02-casos/scripts/preparar.py) | Publica el CSV de 13 columnas de QA junto con la suite ejecutable y sus fuentes. |
| [exportar_azure.py](02-casos/scripts/exportar_azure.py) | Fija el contrato del CSV actual de QA para Azure Test Plans y permite regenerarlo a partir del catálogo. |
| [contracts.py](02-casos/scripts/contracts.py), [json_tools.py](02-casos/scripts/json_tools.py) | Validan los contratos y administran datos y variantes JSON. |
| [mock_data.py](02-casos/scripts/mock_data.py), [openapi_contract.py](02-casos/scripts/openapi_contract.py) | Generan datos sintéticos y validan contra OpenAPI cuando corresponde. |
| [azure_export.py](02-casos/scripts/azure_export.py) | Exportación del CLI avanzado para Azure Test Plans. |
| [promotion.py](02-casos/scripts/promotion.py), [regressions.py](02-casos/scripts/regressions.py) | Administran promociones y el catálogo de regresión del CLI avanzado. |
| [draft_cases.py](02-casos/scripts/draft_cases.py) | Generador experimental de borradores con Ollama. Lee un paquete de RAGFlow verificado. El pase oficial a QA y ejecución se hace con `preparar.py`. |

## 03 · Ejecución y evidencia

| Archivo | Uso |
|---|---|
| [preflight.py](03-ejecuciones/scripts/preflight.py) | Comprueba conectividad, dependencias y variables por caso. |
| [browser_preflight.py](03-ejecuciones/scripts/browser_preflight.py) | Comprueba login, disponibilidad y sonda por actor. Entrega estado de sesión en memoria y bloquea solo los casos dependientes. |
| [ejecutar.py](03-ejecuciones/scripts/ejecutar.py) | Ejecuta la entrega de casos y publica preflight, dictamen y evidencia de los intentos. |
| [qa.py](03-ejecuciones/scripts/qa.py), [workflow.py](03-ejecuciones/scripts/workflow.py) | CLI avanzado heredado de V6 y lógica para congelar planes y ejecutar suites. |
| [runners.py](03-ejecuciones/scripts/runners.py), [browser_steps.py](03-ejecuciones/scripts/browser_steps.py), [ui_walk.py](03-ejecuciones/scripts/ui_walk.py), [database_runner.py](03-ejecuciones/scripts/database_runner.py) | Runners de superficie, interacciones de Playwright y consultas de base de datos. |
| [bindings.py](03-ejecuciones/scripts/bindings.py), [session.py](03-ejecuciones/scripts/session.py), [records.py](03-ejecuciones/scripts/records.py), [audit.py](03-ejecuciones/scripts/audit.py) | Vinculan entorno y suite, gestionan sesiones, registran eventos y auditan evidencia. |
| [publication.py](03-ejecuciones/scripts/publication.py), [management_report.py](03-ejecuciones/scripts/management_report.py), [markdown.py](03-ejecuciones/scripts/markdown.py), [sdd_export.py](03-ejecuciones/scripts/sdd_export.py) | Publican entregas y reportes Markdown y HTML, y exportan propuestas SDD. |
| [release.py](03-ejecuciones/scripts/release.py), [release_cli.py](03-ejecuciones/scripts/release_cli.py), [retest.py](03-ejecuciones/scripts/retest.py), [comparison.py](03-ejecuciones/scripts/comparison.py), [model_quality.py](03-ejecuciones/scripts/model_quality.py) | Operan campañas de release y retest, comparan resultados y evalúan modelos sobre regresiones conocidas. |
| [historial_retest.py](03-ejecuciones/scripts/historial_retest.py) | Compara entregas de V10 y registra decisiones de QA junto con los resultados automáticos y su evidencia. |
| [token_meter.py](03-ejecuciones/scripts/token_meter.py) | Lee los contadores nativos y atribuye el consumo a su conversación o etapa. |
| [benchmark/evaluate.py](03-ejecuciones/scripts/benchmark/evaluate.py), [benchmark_report.py](03-ejecuciones/scripts/benchmark/benchmark_report.py) | Congelan un benchmark, archivan corridas y generan una comparación con evidencia. [Guía del benchmark](03-ejecuciones/scripts/benchmark/README.md) |
| [demo_chatbot.py](03-ejecuciones/scripts/demo_chatbot.py), [test_flujo.py](03-ejecuciones/scripts/test_flujo.py) | Aplicación sintética y pruebas de los contratos entre etapas. |

Las etapas comparten rutas, persistencia y el consolidado de artefactos. Los conectores que usan credenciales resuelven solo las variables declaradas. [rutas.py](scripts/rutas.py) · [soporte.py](scripts/soporte.py) · [consolidar.py](scripts/consolidar.py) · [credenciales.py](scripts/credenciales.py)

El índice y los consolidados comparten el redactor heurístico. Los tres logs incorporan métricas por ID. [higiene.py](scripts/higiene.py) · [metricas_etapa.py](scripts/metricas_etapa.py)

## Versiones anteriores en el repositorio

- `v6/src/` conserva las fuentes de V6 para reproducir sus corridas.
- `historico/Post Harness V2/ragflow-local/` y `ollama-pilot/` conservan los experimentos de instalación, calibración y evaluación. `historico/Post Harness V2/scripts/` conserva los scripts de medición y reportes de ese piloto.
- `scripts/` en la raíz del repositorio conserva el prototipo que validaba, exportaba y corría casos, convertía JUnit y empaquetaba evidencia.
