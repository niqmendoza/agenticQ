# Guía de scripts para QA con Copilot

Esta carpeta es el punto de entrada. Los scripts permanecen en sus carpetas originales: moverlos rompería imports, rutas, reproducción e integridad de evidencias. No hay copias adicionales. Empezá por [INICIO-COPILOT.md](INICIO-COPILOT.md) y pasale a Copilot [PROMPT-COPILOT.md](PROMPT-COPILOT.md).

## Qué hace el flujo

1. Recupera documentación local con `brain.py` o desde RAGFlow con `retrieve.py`.
2. Copilot puede proponer casos a partir de esa evidencia; alternativamente `draft_cases.py` genera borradores con Ollama local. QA revisa los casos.
3. Copilot puede implementar pruebas en el proyecto de la aplicación y ejecutar el comando real de su framework, en un entorno y con datos autorizados. **Ningún script de este repositorio ejecuta pruebas funcionales de la aplicación ni publica en Azure Test Plans.** Los tests de este repositorio validan sus propias herramientas. No se inventaron URL, credenciales ni comandos de Coelsa.

## Inventario de scripts

Rutas relativas a la raíz del repositorio. Para opciones ejecutá el script con `--help` cuando lo admita; los scripts de apoyo se invocan mediante la interfaz o guía indicada. Se agrupan archivos con la misma función para mantener el inventario legible.

| Ruta | Uso |
| --- | --- |
| `Post Harness V2/scripts/brain.py` | Navegador local: `index`, `pack`, `show`, `headings`, `links`, `verify`, `status`. Ver [uso](../Post%20Harness%20V2/README.md). |
| `Post Harness V2/scripts/document_utils.py` | Soporte interno de lectura y fragmentación de `brain.py`; no se invoca directamente. |
| `Post Harness V2/scripts/retrieve.py` | Consulta RAGFlow y guarda contexto `qa-context/1`; ver [guía](../Post%20Harness%20V2/GUIA-CONTEXTO-RAGFLOW.md). |
| `Post Harness V2/scripts/ragflow_client.py` | Cliente HTTP usado por `retrieve.py`; no es un ejecutor de pruebas. |
| `Post Harness V2/scripts/context_packet.py` | Empaqueta fragmentos y fuentes; lo usa `retrieve.py`. |
| `Post Harness V2/scripts/verify_context.py` | `python3 "Post Harness V2/scripts/verify_context.py" CONTEXTO.json`; comprueba integridad, no significado. |
| `Post Harness V2/scripts/draft_cases.py` | Genera borradores con contexto RAGFlow y Ollama local; `--help` y [guía](../Post%20Harness%20V2/GUIA-GENERACION-4B.md). |
| `Post Harness V2/scripts/collect_metrics.py`, `extract_usage.py`, `extract_transcript.py` | Recopilan telemetría y transcripciones del ensayo; uso en [explicación](../Post%20Harness%20V2/EXPLICACION.md). |
| `Post Harness V2/scripts/build_report.py`, `build_explanation.py` | Construyen el reporte y explicación del ensayo V2, desde `Post Harness V2`. |
| `Post Harness V2/scripts/verify_html.cjs` | Verifica el HTML histórico; requiere Playwright y Chromium, ver su código antes de ejecutar (escribe capturas en evidencias). |
| `Post Harness V2/ragflow-local/manage.py`, `setup_api.py`, `check_api.py` | Gestionan, cargan y diagnostican el piloto RAGFlow; [instrucciones y requisitos](../Post%20Harness%20V2/ragflow-local/README.md). La carga predeterminada es el corpus congelado, no cualquier aplicación. |
| `Post Harness V2/ragflow-local/evaluate_retrieval.py`, `calibrate_retrieval.py`, `evaluate_adapter.py` | Evalúan y calibran recuperación/adaptador; ver [guía RAGFlow](../Post%20Harness%20V2/ragflow-local/README.md). |
| `Post Harness V2/ragflow-local/build_test_report.py` | Genera el reporte de evaluación de recuperación; ver guía RAGFlow. No ejecuta pruebas de producto. |
| `Post Harness V2/ollama-pilot/evaluate_grounded_drafts.py`, `evaluate_small_models.py` | Ensayos del generador y modelos locales; [guía](../Post%20Harness%20V2/ollama-pilot/README.md). |
| `Post Harness/scripts/brain.py`, `read_full.py`, `snapshot.py` | Herramientas históricas de navegación, lectura completa y snapshot V1; ver [README histórico](../Post%20Harness/README.md). |
| `Post Harness/scripts/measure.py`, `extract_usage.py`, `extract_transcript.py`, `report.py`, `validate_evidence.py` | Medición, exportación, reporte y validación del ensayo histórico; ver README histórico. |
| `qa-process-prototype/scripts/validate-model.mjs`, `check-milestones.mjs`, `check-process-flow.mjs` | Validan datos y flujo del prototipo visual; usar los comandos de su [README](../qa-process-prototype/README.md). |
| `presentacion/src/construir.py` y `presentacion/archivo-*/construir.py` | Generan la presentación y versiones históricas; no forman parte del flujo de pruebas. |
| `Post Harness V2/ollama-pilot/results/*/*.py` | Copias congeladas de prototipos del ensayo; referencia histórica, no puntos de entrada actuales. |

Las suites `Post Harness/tests/` y `Post Harness V2/tests/` contienen pruebas de las herramientas, no de la aplicación. Preservá las evidencias y consultá las guías antes de repetir ensayos que escriben archivos.
