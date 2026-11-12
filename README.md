# QA agentizada

[Framework V4 y piloto local con PappU](v4/README.md)

Herramientas, documentación y evidencias del proyecto de QA agentizada. La versión de trabajo actual es **V4**.

## Dónde está cada cosa

| Carpeta | Contenido |
| --- | --- |
| [qa-v3](qa-v3/README.md) | Motor documental, registro de casos y ejecuciones, `log.md`, instrucciones y pruebas de la V3. Versión anterior y sus instrucciones. |
| [docs](docs/README.md) | Proceso de QA, relevamiento, entrevistas y plantillas. |
| [informes](informes/) | Guía visual, mapa e informes del proyecto. Ver [evolución de QA](informes/Reporte-evolucion-QA.html). |
| [scripts](scripts/README.md) | Herramientas del flujo anterior y sus pruebas. |
| [historico](historico/) | Ensayos V1 y V2, evidencias y copias históricas. Se conserva su contenido. |
| [presentacion](presentacion/) | Presentaciones y sus recursos. |
| [qa-process-prototype](qa-process-prototype/README.md) | Prototipo interactivo del proceso. |
| [Plantilla-diagramas](Plantilla-diagramas/) | Plantilla y kit de arquitectura. |

## Empezar con V3

Leer la [guía de V3](qa-v3/README.md) y el [protocolo del agente](qa-v3/docs/PROTOCOLO-AGENTE.md). Se necesita Python 3.10+, una carpeta local de documentos del segundo cerebro y un directorio de trabajo fuera de ese corpus. El agente debe tener acceso autorizado a la aplicación y a las herramientas de prueba para ejecutar el recorrido real.

```sh
cd qa-v3
python3 -m unittest discover -s tests -v
```

La generación de casos, su revisión semántica y las pruebas de producto requieren un agente; indexar o recuperar documentos no demuestra cobertura ni aprobación de una release.

## Material anterior

- [Reporte y documentación V2](historico/Post%20Harness%20V2/README.md): ensayo documental, adaptador RAGFlow y evidencias.
- [Ensayo V1](historico/Post%20Harness/README.md): navegador documental y comparación original.
- [Guía visual anterior](informes/Inicio-QA.html) y [mapa del proceso](informes/Mapa-QA-agentizada.html).

El material histórico conserva sus resultados y limitaciones; no son pruebas de la aplicación actual. Las sesiones y credenciales locales no se incluyen en Git.
