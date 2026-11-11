# Guía de scripts para QA con Copilot

Esta carpeta es el punto de entrada. Los scripts permanecen en sus carpetas originales: moverlos rompería imports, rutas, reproducción e integridad de evidencias. No hay copias adicionales. Para empezar sin programar, seguí [GUIA-QA.md](GUIA-QA.md) y copiá [PROMPT-COPILOT.md](PROMPT-COPILOT.md).

La [guía de flujo portable](FLUJO-PORTABLE.md) incluye configuración, ejecución con evidencia y un ejemplo integral local.

## Qué hace el flujo

1. Recupera documentación local con `brain.py` o desde RAGFlow con `retrieve.py`.
2. Copilot puede proponer casos a partir de esa evidencia; alternativamente `draft_cases.py` genera borradores con Ollama local. QA revisa los casos.
3. Copilot puede implementar pruebas en el proyecto de la aplicación y ejecutar el comando real de su framework, en un entorno y con datos autorizados. **`run_tests.py` ejecuta el comando de pruebas que se le indique, pero no crea ni adapta las pruebas por sí solo.** Ningún script publica en Azure Test Plans. Los tests de este repositorio validan sus propias herramientas. No se inventaron URL, credenciales ni comandos de Coelsa.

## Inventario de scripts

Rutas relativas a la raíz del repositorio. Para opciones ejecutá el script con `--help` cuando lo admita; los scripts de apoyo se invocan mediante la interfaz o guía indicada. Se agrupan archivos con la misma función para mantener el inventario legible.

| Ruta | Uso |
| --- | --- |
| `scripts/empaquetar_evidencia.py`, `scripts/verificar_evidencia.py` | Reúnen archivos seleccionados y verifican sus hashes; ver [guía de evidencia](VALIDACION-Y-EVIDENCIA.md). |
| `scripts/resultados_junit.py` | Vincula resultados individuales JUnit con casos mediante un mapa explícito y revisado. |
| `scripts/validar_casos.py` | Comprueba estructura y citas literales; la revisión semántica y humana sigue pendiente. |
| `scripts/regresion.py` | Registra casos revisados y prepara planes por release sin ejecutar ni regenerar casos. |
| `scripts/exportar.py` | Prepara CSV de Azure, CSV para Excel y trazabilidad; no importa ni infiere resultados. |
| `scripts/run_tests.py` | Ejecuta un comando explícito en el proyecto y guarda resultado, salida y errores; ver [flujo portable](FLUJO-PORTABLE.md). |
| `scripts/ejemplo/` y `scripts/tests/` | Aplicación y documentos sintéticos; pruebas del ejecutor y flujo integral, no de Coelsa. |
| `historico/Post Harness V2/scripts/brain.py` | Navegador local: `index`, `pack`, `show`, `headings`, `links`, `verify`, `status`. Ver [uso](../historico/Post%20Harness%20V2/README.md). |
| `historico/Post Harness V2/scripts/document_utils.py` | Soporte interno de lectura y fragmentación de `brain.py`; no se invoca directamente. |
| `historico/Post Harness V2/scripts/retrieve.py` | Consulta RAGFlow y guarda contexto `qa-context/1`; ver [guía](../historico/Post%20Harness%20V2/GUIA-CONTEXTO-RAGFLOW.md). |
| `historico/Post Harness V2/scripts/ragflow_client.py` | Cliente HTTP usado por `retrieve.py`; no es un ejecutor de pruebas. |
| `historico/Post Harness V2/scripts/context_packet.py` | Empaqueta fragmentos y fuentes; lo usa `retrieve.py`. |
| `historico/Post Harness V2/scripts/verify_context.py` | `python3 "historico/Post Harness V2/scripts/verify_context.py" CONTEXTO.json`; comprueba integridad, no significado. |
| `historico/Post Harness V2/scripts/draft_cases.py` | Genera borradores con contexto RAGFlow y Ollama local; `--help` y [guía](../historico/Post%20Harness%20V2/GUIA-GENERACION-4B.md). |
| `historico/Post Harness V2/scripts/collect_metrics.py`, `extract_usage.py`, `extract_transcript.py` | Recopilan telemetría y transcripciones del ensayo; uso en [explicación](../historico/Post%20Harness%20V2/EXPLICACION.md). |
| `historico/Post Harness V2/scripts/build_report.py`, `build_explanation.py` | Construyen el reporte y explicación del ensayo V2, desde `Post Harness V2`. |
| `historico/Post Harness V2/scripts/verify_html.cjs` | Verifica el HTML histórico; requiere Playwright y Chromium, ver su código antes de ejecutar (escribe capturas en evidencias). |
| `historico/Post Harness V2/ragflow-local/manage.py`, `setup_api.py`, `check_api.py` | Gestionan, cargan y diagnostican el piloto RAGFlow; [instrucciones y requisitos](../historico/Post%20Harness%20V2/ragflow-local/README.md). La carga predeterminada es el corpus congelado, no cualquier aplicación. |
| `historico/Post Harness V2/ragflow-local/evaluate_retrieval.py`, `calibrate_retrieval.py`, `evaluate_adapter.py` | Evalúan y calibran recuperación/adaptador; ver [guía RAGFlow](../historico/Post%20Harness%20V2/ragflow-local/README.md). |
| `historico/Post Harness V2/ragflow-local/build_test_report.py` | Genera el reporte de evaluación de recuperación; ver guía RAGFlow. No ejecuta pruebas de producto. |
| `historico/Post Harness V2/ollama-pilot/evaluate_grounded_drafts.py`, `evaluate_small_models.py` | Ensayos del generador y modelos locales; [guía](../historico/Post%20Harness%20V2/ollama-pilot/README.md). |
| `historico/Post Harness/scripts/brain.py`, `read_full.py`, `snapshot.py` | Herramientas históricas de navegación, lectura completa y snapshot V1; ver [README histórico](../historico/Post%20Harness/README.md). |
| `historico/Post Harness/scripts/measure.py`, `extract_usage.py`, `extract_transcript.py`, `report.py`, `validate_evidence.py` | Medición, exportación, reporte y validación del ensayo histórico; ver README histórico. |
| `qa-process-prototype/scripts/validate-model.mjs`, `check-milestones.mjs`, `check-process-flow.mjs` | Validan datos y flujo del prototipo visual; usar los comandos de su [README](../qa-process-prototype/README.md). |
| `presentacion/src/construir.py` y `presentacion/archivo-*/construir.py` | Generan la presentación y versiones históricas; no forman parte del flujo de pruebas. |
| `historico/Post Harness V2/ollama-pilot/results/*/*.py` | Copias congeladas de prototipos del ensayo; referencia histórica, no puntos de entrada actuales. |

Las suites `historico/Post Harness/tests/` y `historico/Post Harness V2/tests/` contienen pruebas de las herramientas, no de la aplicación. Preservá las evidencias y consultá las guías antes de repetir ensayos que escriben archivos.
