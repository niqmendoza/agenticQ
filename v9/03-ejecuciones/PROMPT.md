# Etapa 03 · Diagnosticar, ejecutar y emitir el dictamen

Trabajá desde el directorio que contiene `v9/`, con el intérprete de la VM. Usá la carpeta completa publicada por el 02 y su alcance frontend, API o ambos. Tomá las credenciales de las variables ya inyectadas o de `v9/credenciales.txt`. Pasale al script solo la ruta con `--credenciales` si QA lo guardó en otra ubicación. Los valores se cargan en el proceso del runner y se mantienen fuera de la conversación y los artefactos.

```text
ENTREGA_CASOS = [carpeta con suite.json y entrega.json]
ID_PREFLIGHT = [ID nuevo para el diagnóstico]
ID_EJECUCION = [ID nuevo para los intentos]
BUILD_DESPLEGADO = [versión confirmada]
BUILD_REF = [commit, digest de imagen o evidencia del despliegue]
NAVEGADOR = [perfil del servidor o Chrome visible si QA lo pidió]
```

## Confirmar el entorno antes de lanzar casos

```sh
python v9/03-ejecuciones/scripts/ejecutar.py procesar --id ID_PREFLIGHT --casos "ENTREGA_CASOS" --build "BUILD_DESPLEGADO" --build-ref "BUILD_REF" --solo-preflight
```

Revisá `preflight.json`. Agrupa navegador, conectividad del origen y variables faltantes por caso. El diagnóstico deja cero intentos. Confirmá el build con el despliegue, y el acceso y los roles con el perfil de QA. Si el build de la entrega coincide, podés usar sus campos. `--chrome-visible` necesita sesión gráfica. Si faltan credenciales, indicá solo los nombres. Si algunos casos están habilitados, podés correrlos y reportar aparte los bloqueados por preflight.

## Ejecutar y comprobar

```sh
python v9/03-ejecuciones/scripts/ejecutar.py procesar --id ID_EJECUCION --casos "ENTREGA_CASOS" --build "BUILD_DESPLEGADO" --build-ref "BUILD_REF"
```

- Para frontend, abrí la evidencia de Playwright. Comprobá el paso real y el resultado visible en el control esperado. Revisá mensajes del asistente, estado de adjuntos o evidencia de descarga según el criterio. Interpretá el HTTP de navegación y el de una operación con sus etiquetas.
- Para API, cotejá método, ruta, actor y respuesta. Para DB, cotejá la lectura autorizada. Si falla un selector, registrá ID, paso, control, causa y coincidencias. Si requiere cambiar el diseño, devolvelo al 02 y ejecutá una entrega nueva.
- Informá build, resultado de casos, cobertura por superficie y pendientes de diseño. Las aserciones fallidas, los bloqueos previos y lo inconcluso tienen estados distintos. Enlazá evidencia, HTML, JUnit y ZIP cuando se publiquen.

Con telemetría nativa, registrá el corte con `ejecutar.py medir`. Cerrá con `log03.md` de todos los diagnósticos, fallos y corridas de este encargo.

```sh
python v9/03-ejecuciones/scripts/ejecutar.py consolidar --id ID_PREFLIGHT --id ID_EJECUCION
```
