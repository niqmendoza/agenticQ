# agenticQ

Código, documentación, prototipos y evidencias del trabajo de QA agentizada. Este repositorio reúne el material elaborado hasta el 29 de octubre de 2026.

## Usar con GitHub Copilot

**[Abrir guía visual para empezar · QA](Inicio-QA.html)**

Para empezar sin programar, seguí [scripts/GUIA-QA.md](scripts/GUIA-QA.md) y copiá el prompt; la configuración técnica está en [scripts/INICIO-COPILOT.md](scripts/INICIO-COPILOT.md). El [inventario de scripts](scripts/README.md) explica qué se ejecuta y dónde está; la generación de borradores y la ejecución de pruebas de la aplicación son etapas distintas.

## Por dónde empezar

| Material | Contenido |
| --- | --- |
| [Hito 2](Hito-2.html) | RAGFlow local, recuperación por API, contexto compacto y avance técnico registrado en el mapa. |
| [Reporte visual V2](Post%20Harness%20V2/reporte-v2.html) | Comparación de las tres iteraciones: lectura completa, scripts V1 y scripts V2. Consumo, recuperación del contexto y cambios. |
| [Explicación técnica V2](Post%20Harness%20V2/EXPLICACION.md) | Metodología, resultados, límites y reproducción del ensayo. |
| [Reporte original](Post%20Harness/reporte.html) | Primera comparación y sus evidencias, conservadas sin cambios. |
| [Documentación de QA](docs/README.md) | Relevamiento, proceso, entrevistas, decisiones y plantillas. |
| [Presentación](presentacion/QA-agentizada.html) | Presentación HTML, con fuentes, recursos, capturas, PDF y versiones anteriores en su carpeta. |
| [Mapa de QA](Mapa-QA-agentizada.html) | Mapa visual del proceso y las propuestas. |
| [Prototipo interactivo](qa-process-prototype/README.md) | Aplicación React/Vite con código fuente y versión compilada. |
| [Plantilla de arquitectura](Plantilla-diagramas/Plantilla-Arquitectura.html) | Plantilla HTML, instrucciones y prompt para completarla. |

Para ver los reportes y presentaciones con su diseño, cloná el repositorio y abrí el HTML desde tu equipo. Conservá la estructura de carpetas para que funcionen los enlaces a las evidencias. GitHub muestra el código fuente de los HTML.

```sh
git clone https://github.com/niqmendoza/agenticQ.git
cd agenticQ
open "Post Harness V2/reporte-v2.html"
```

`open` corresponde a macOS; en otros sistemas se puede abrir el archivo con el navegador.

## Scripts y ensayos

- [Post Harness V1](Post%20Harness/README.md): navegador documental inicial, pruebas y ensayo congelado.
- [Post Harness V2](Post%20Harness%20V2/README.md): consultas agrupadas, recuperación por relaciones, sesiones con deduplicación, presupuestos y validación de citas. Incluye el adaptador de RAGFlow y su [guía de contexto](Post%20Harness%20V2/GUIA-CONTEXTO-RAGFLOW.md).
- [Próximo ensayo con Saluki/Ollama](Post%20Harness%20V2/ollama-pilot/README.md): evaluación de la Mac, perfil de ejecución y plantilla experimental; modelo todavía sin instalar ni ejecutar.
- Cada carpeta conserva sus scripts, pruebas, instrucciones para el agente, evidencias y manifiesto de integridad.
- Los snapshots documentales del primer ensayo se incluyen porque respaldan sus citas y permiten revisar la comparación.

El núcleo de los navegadores usa Python 3.10+ y biblioteca estándar. La medición y los límites por tokens requieren las dependencias de `requirements-medicion.txt` de cada ensayo. Las instrucciones completas están en sus respectivos README.

```sh
cd "Post Harness V2"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-medicion.txt
.venv/bin/python -m unittest discover -s tests -v
```

Los resultados comparan ejecuciones exploratorias sobre un mismo mock; no prueban equivalencia de calidad ni una mejora causal generalizable. Los contadores nativos y los conteos de contenido se presentan por separado. Ver la [explicación técnica](Post%20Harness%20V2/EXPLICACION.md) para interpretar las cifras.

## Qué se conserva

Se incluyen código fuente, distribuciones HTML, documentación Markdown, presentaciones, PDF, capturas, ZIP y bases SQLite de evidencias. También se conservan copias y versiones históricas existentes.

Se excluyen entornos virtuales, dependencias instaladas, cachés, archivos del sistema y archivos de credenciales locales. Los logs y payloads publicados dentro de las evidencias son los artefactos exportados del ensayo; no se incluyen los rollouts privados originales de Codex.
