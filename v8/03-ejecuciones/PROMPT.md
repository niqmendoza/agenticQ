# Etapa 3 · Ejecutar la suite y emitir el dictamen

Copilot, ejecutá `ejecutar.py` desde la terminal con el Python preparado en el servidor. Usá la carpeta completa publicada por `preparar.py`. El script valida la entrega, hace el preflight y llama al runner que corresponde a cada caso.

```text
ENTREGA_CASOS = [carpeta con suite.json y entrega.json]
ID_EJECUCION = [ID nuevo]
BUILD_DESPLEGADO = [versión confirmada en QA]
NAVEGADOR = [perfil del servidor o Chrome visible si QA lo pidió]
```

## Lanzar la corrida

Contrastá el entorno, el build, los actores y los datos sintéticos con el encargo. Desde la carpeta que contiene `v8/`, reemplazá los marcadores y ejecutá el comando.

```sh
python v8/03-ejecuciones/scripts/ejecutar.py procesar --id "ID_EJECUCION" --casos "ENTREGA_CASOS"
```

Si el build confirmado difiere del original en el mismo entorno, pasá `--build "BUILD_DESPLEGADO"`. Agregá `--chrome-visible` si QA pide ver Chrome y tenés sesión gráfica. Para los casos frontend, seguí las acciones de Playwright de la suite completa, incluida la comprobación del resultado en pantalla. La prueba del recorrido debe quedar en los intentos registrados por el runner.

## Verificar la evidencia y cerrar

1. Leé el código de salida, `dictamen.json` y `logs/ID/INTENTO/resumen.json`. Si hay un error de entrada o del runner, revisá `runner.log` cuando exista. Para cero intentos, identificá el requisito faltante en `preflight.json`. Si se puede resolver en ese entorno, repetí con un ID nuevo. Si hace falta cambiar un control o un paso, devolvé a diseño el ID, el paso y la evidencia.
2. Para frontend, cruzá `casos_ui_con_interaccion_observada` y `casos_ui_aprobados` con `cobertura_por_recorrido`. Abrí la evidencia del caso para confirmar la acción solicitada y el resultado por criterio. Declaralo aprobado solo si están registrados la interacción y el esperado satisfecho. Para un fallo, citá el esperado y lo observado. Para un bloqueo, indicá qué recorrido quedó inconcluso.
3. Informá el build, el dictamen y el estado de los recorridos solicitados. Enlazá el log y, cuando se publiquen, el HTML, JUnit y ZIP. Con telemetría nativa, registrá el corte con `ejecutar.py medir`. [Medición por etapa](../README.md#logs-consumos-y-repetición)
