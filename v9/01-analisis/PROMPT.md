# Etapa 01 · Analizar el segundo cerebro

Trabajá desde el directorio que contiene `v9/`. Usá la terminal para ejecutar los scripts y pasá al siguiente agente la entrega publicada.

```text
APLICACION = [nombre visible, admite espacios y puntos]
APP_ID = [opcional, identificador técnico]
SUPERFICIES = [frontend | api | ambas. db si se pide lectura directa]
ENTORNO =
BUILD =
BUILD_REF = [commit, digest o referencia del despliegue, si está disponible]
MODO_AUTH_ESPERADO = [login local, SSO, acceso anónimo u otro aprobado para ese entorno]
AREA_QA = [ruta de área confirmada para el CSV, si ya está disponible]
CORPUS = [carpeta del segundo cerebro]
RECORRIDOS = [tareas que QA quiere comprobar]
RECORRIDOS_PRIORIZADOS = [IDs que deben quedar listos en esta corrida]
```

## Delimitar y validar

Armá `encargo.json` a partir del [ejemplo](ejemplos/encargo.demo.json). `app` conserva el nombre que dio QA. El script deriva `app_id` cuando falta. Fijá la superficie de cada recorrido. Para `ambas`, asigná IDs distintos a las verificaciones de frontend y API. Usá el mismo `grupo` si comprueban la misma función. La red que dispara la UI forma parte de su prueba frontend. La prueba directa de API lleva su propio recorrido.

Aprovechá los datos acordados. Pedí el alcance cuando falte elegir superficie o prioridad y eso cambie las pruebas. El corpus y los documentos adjuntos son fuentes de evidencia. En esta etapa el trabajo es documental. Un smoke sobre el entorno requiere que QA lo pida como tarea y se registra por separado como observación.

```sh
python v9/01-analisis/scripts/analizar.py procesar --id ID-encargo --validar-encargo --encargo "ENCARGO"
```

## Recuperar y cerrar reglas

Agrupá consultas por objetivo. Conservá el índice si vas a consultar secciones adicionales. Revisá `analisis.json` y los extractos pertinentes de `fuentes/`.

```sh
python v9/01-analisis/scripts/analizar.py procesar --id ID-contexto --encargo "ENCARGO_NORMALIZADO" --corpus "CORPUS" --conservar-indice
```

Usá `brain.py` para ubicar encabezados, enlaces o rangos en el índice. Para una cita fuera del paquete, agregá su rango a una nueva entrega mediante el SQLite de la revisión conservada. Repetí `--agregar-rango` según corresponda. Si el corpus cambió, retomá la recuperación. [Navegación del segundo cerebro](../INVENTARIO-SCRIPTS.md#navegación-puntual-con-el-motor-local)

```sh
python v9/01-analisis/scripts/analizar.py procesar --id ID-ampliado --base "RUTA_CONTEXTO" --indice "NAV/indice.sqlite" --agregar-rango "ARCHIVO_RELATIVO" DESDE HASTA
```

Armá la [revisión](ejemplos/revision.demo.json) con actor, condición, esperado y citas al archivo original. Si hay contradicción, registrá ambas referencias y la decisión en `pendiente`. Para RAGFlow usá las herramientas del inventario cuando corresponda al piloto. El pase a casos lo publica `analizar.py`.

```sh
python v9/01-analisis/scripts/analizar.py procesar --id ID-analisis --base "RUTA_CONTEXTO_FINAL" --revision "REVISION"
```

Entregá la carpeta con `reglas.json`, `fuentes/` y `entrega.json`. Indicá pendientes. Con telemetría nativa, registrá el corte con `analizar.py medir`. Cerrá con `log01.md` de toda la corrida, incluyendo los IDs de validación, recuperación, ampliaciones, fallos y cierre que realmente se usaron.

```sh
python v9/01-analisis/scripts/analizar.py consolidar --id ID-encargo --id ID-contexto --id ID-analisis
```
