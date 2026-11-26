# Etapa 03 · Diagnosticar, ejecutar y emitir el dictamen

Trabajá desde el directorio que contiene `v10/`, con el intérprete de la VM. Usá la carpeta completa publicada por el 02 y su alcance frontend, API o ambos. Tomá las credenciales de las variables ya inyectadas o de `v10/credenciales.txt`. Pasale al script solo la ruta con `--credenciales` si QA lo guardó en otra ubicación. Los valores se cargan en el proceso del runner y se mantienen fuera de la conversación y los artefactos.

```text
ENTREGA_CASOS = [carpeta con suite.json y entrega.json]
ID_PREFLIGHT = [opcional, ID nuevo si QA pide solo diagnóstico]
ID_EJECUCION = [ID nuevo para los intentos]
BUILD_DESPLEGADO = [versión confirmada]
BUILD_REF = [commit, digest de imagen o evidencia del despliegue]
NAVEGADOR = [perfil del servidor o Chrome visible si QA lo pidió]
```

## Ejecutar con diagnóstico incluido

```sh
python v10/03-ejecuciones/scripts/ejecutar.py procesar --id ID_EJECUCION --casos "ENTREGA_CASOS" --build "BUILD_DESPLEGADO" --build-ref "BUILD_REF"
```

Confirmá el build, los accesos y los roles del perfil. Si el build de la entrega coincide, podés usar sus campos. `--chrome-visible` necesita sesión gráfica. Si faltan credenciales, informá solo los nombres. La misma corrida comprueba los requisitos técnicos y las sesiones declaradas. Cada sesión valida el login, el control listo y la sonda opcional. Si falla, el motor conserva el motivo y saltea ese grupo y sus dependientes. Los casos independientes siguen.

Usá `--solo-preflight` con un ID dedicado si QA pide diagnóstico sin casos. Consume una sesión por actor declarado. La corrida siguiente arranca su propia sesión.

```sh
python v10/03-ejecuciones/scripts/ejecutar.py procesar --id ID_PREFLIGHT --casos "ENTREGA_CASOS" --solo-preflight
```

## Revisar evidencia y documentar retests

- Abrí `preflight.json`. Para el login usá el método, ruta, estado HTTP y causa registrados. Si aparece `limite_login`, informá qué grupos quedaron sin intento. Si el login pasa y falta el control listo, revisá la navegación permitida y el selector diseñado. Los casos de login o logout usan su contexto nuevo.
- Para frontend, abrí la evidencia de Playwright. Comprobá el recorrido, el modelo verificado, los guardas de estado, el turno nuevo, los resultados de adjuntos o la descarga según el caso. Registrá cada caso sin intento por separado.
- Para API, cotejá método, ruta, actor y respuesta. Para DB, cotejá la lectura autorizada. Si falla un selector, registrá ID, paso, control, causa y coincidencias. Si requiere cambiar el diseño, devolvelo al 02 y ejecutá una entrega nueva.
- Informá build, resultado de casos, cobertura por superficie y pendientes de diseño. Las aserciones fallidas, los bloqueos previos y lo inconcluso tienen estados distintos. Enlazá evidencia, HTML, JUnit y ZIP cuando se publiquen.

Para relacionar dos entregas, usá el script de historial. Si QA aporta una decisión manual, adjuntala con `--disposicion`. Ese registro conserva los dos estados automáticos, las evidencias y la decisión de QA. [Formato de decisiones](../README.md#retest-y-decisión-manual)

```sh
python v10/03-ejecuciones/scripts/historial_retest.py --anterior "ENTREGA_ANTERIOR" --actual "ENTREGA_ACTUAL"
```

Con telemetría nativa, registrá el corte con `ejecutar.py medir`. Usá `metricas-etapa.json` para informar tiempos, reintentos, causas y tokens observados. Cerrá con `log03.md` de todos los IDs realmente usados para este encargo.

```sh
python v10/03-ejecuciones/scripts/ejecutar.py consolidar --id ID_PREFLIGHT --id ID_EJECUCION
```
