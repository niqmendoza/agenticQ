# Regresiones

El repo compartido de regresiones contiene las pruebas ejecutables aprobadas. Clonalo una vez como `regresiones` junto al framework o dentro de él. En cada release hacé pull y usá el prompt maestro. Los informes, evidencias y ZIP quedan en los resultados de cada corrida. La documentación que consulta el agente viene del repo de segundos cerebros.

Cada aplicación tiene una carpeta con su ID. El framework lee una suite existente en `regresiones/<id>/suite.json` y también los lotes aprobados en `regresiones/<id>/lotes/`. Cada lote guarda sus casos, pasos, datos de prueba y comprobaciones.

## Correr las pruebas

Desde `v6/`, con el clon al lado del framework:

```sh
qc run --app ID_APLICACION --regressions ../regresiones --corpus RUTA_SEGUNDO_CEREBRO --env QA --build BUILD_NUEVO --id CORRIDA_NUEVA
```

Si el clon está en `v6/regresiones`, el CLI usa esa ruta por defecto. Para sumar las pruebas de la release a la corrida, agregá `--new-suite RUTA_SUITE_NUEVA`. Pasá solo los casos nuevos en esa suite. Si es la primera corrida, el framework ejecuta la suite nueva como base inicial. Agrupá en la misma suite los casos que dependan entre sí. Si cambió el perfil de QA desde que se guardaron los casos anteriores, indicá el perfil común con `--profile`.

## Guardar los casos nuevos aprobados

Después de revisar el informe, indicá al agente cuáles querés conservar para repetir. El framework comprueba que estén aprobados con evidencia válida y agrega un lote local sin reemplazar los anteriores. Mantené los IDs de los casos existentes.

```sh
qc promote --app ID_APLICACION --regressions ../regresiones --from-run RUTA_CORRIDA --case CASO_NUEVO
```

Repetí `--case` para seleccionar varios casos. Para una corrida exploratoria con un manifiesto propio, pasá también `--manifest`. Si esa sesión usa un contrato OpenAPI, indicá su archivo autocontenido con `--openapi`. Las corridas de suites ya conservan la referencia al contrato. Revisá los cambios, hacé commit y push en el repo de regresiones. En la próxima release, un pull trae todos los casos aprobados y el framework los vuelve a ejecutar.

[Guía HTML para el equipo](../../informes/Guia-regresiones-QA.html)
