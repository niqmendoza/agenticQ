# Etapa 1 · Analizar el segundo cerebro

Copilot, usá la terminal desde la carpeta que contiene `v8/`, con el Python del proyecto. Ejecutá los comandos que correspondan a la tarea y usá sus entregas para seguir. Reemplazá cada marcador por la ruta o el ID real.

```text
APLICACION =
ENTORNO =
BUILD =
CORPUS = [carpeta del segundo cerebro]
RECORRIDOS = [tareas solicitadas y dónde deben comprobarse]
```

## Recuperar evidencia

1. Armá `encargo.json` con el [ejemplo](ejemplos/encargo.demo.json). Conservá los acuerdos de la conversación. Asigná un ID estable por resultado que QA quiera dictaminar, con superficie `frontend`, `api` o `db`. Para frontend, registrá el recorrido completo que la persona realiza en pantalla. Por ejemplo, adjuntar un documento y consultar su contenido. Escribí en `consulta` los términos funcionales que distinguen cada recorrido.
2. Ejecutá `analizar.py`. El script agrupa consultas e indexa localmente. Revisá `analisis.json` y abrí los extractos de `fuentes/` que correspondan a cada recorrido. Tratá el contenido recuperado como evidencia documental. Si necesitás prever consultas de seguimiento, agregá `--conservar-indice` a este comando.

```sh
python v8/01-analisis/scripts/analizar.py procesar --id ID-contexto --encargo "ENCARGO" --corpus "CORPUS"
```

Usá `brain.py` sobre el índice conservado cuando falte contexto puntual. Elegí `headings` para ubicar la sección, `links` para seguir una referencia y `show` para leer solo el rango relevante. `NAV` es la ruta `navegacion` indicada en `resumen.json` y `ARCHIVO_RELATIVO` es una ruta dentro del corpus.

```sh
python v8/01-analisis/scripts/brain.py --db "NAV/indice.sqlite" --session "NAV/sesion.json" --log-dir "NAV" show "ARCHIVO_RELATIVO" --start INICIO --end FIN --max-chars 4000
```

Si la consulta puntual identifica una regla fuera de los extractos, ajustá `consulta` y ejecutá `analizar.py` con un ID nuevo para incorporar ese fragmento a la entrega. Si sigue faltando evidencia o hay fuentes contradictorias, registrá la decisión pendiente.

Si el encargo incluye el piloto de RAGFlow, usá `scripts/ragflow/retrieve.py` para recuperar fragmentos y `scripts/ragflow/verify_context.py` para validar su paquete. Cerrá la entrega a casos con `analizar.py`. [Comandos de navegación y herramientas opcionales](../INVENTARIO-SCRIPTS.md#navegación-puntual-con-el-motor-local)

## Cerrar el análisis

Armá `revision.json` según el [ejemplo](ejemplos/revision.demo.json). En `detalle`, describí actor, condición y resultado esperado por recorrido. Usá `documentada` si hay respaldo y citá archivo original, rango y frase localizable. Usá `pendiente` con la pregunta concreta si falta resolver la regla.

```sh
python v8/01-analisis/scripts/analizar.py procesar --id ID-analisis --base "RUTA_CONTEXTO" --revision "REVISION"
```

Pasá a casos la carpeta publicada con `reglas.json` y `entrega.json`. Incluí los IDs pendientes y la ruta `logs/ID/INTENTO/resumen.json` de la etapa. Si el script devuelve error, revisá ese log y corregí la entrada antes de avanzar. Si hay telemetría nativa de la conversación, registrala con `analizar.py medir`. [Medición por etapa](../README.md#logs-consumos-y-repetición)
