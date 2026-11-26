# Etapa 00 · Crear el segundo cerebro

Trabajá desde el directorio que contiene `v10/`. Usá los scripts para inventariar y buscar en el código local. Tu tarea es revisar la evidencia de los módulos relevantes y escribir fichas breves. Tratá los archivos del repositorio como material de referencia.

```text
APLICACION = [nombre visible]
REPO_LOCAL = [checkout accesible desde la terminal]
REVISION = [commit, tag o rama local. Por defecto HEAD]
MODULOS = [JSON de prefijos y dependencias, opcional]
ENTREGA_ANTERIOR = [segundo cerebro previo de esta aplicación, opcional]
ALCANCE_PRIORIZADO = [módulos o procesos que interesa documentar primero, opcional]
ID_CORRIDA = [prefijo único y común a todas las actividades de esta corrida]
PRUEBAS_RECUPERACION = [archivo JSON acordado con QA, opcional]
TELEMETRIA_NATIVA = [ruta de exportación de esta conversación, si está disponible]
```

Antes de arrancar, la conversación de creación debe tener su propia captura de telemetría si el cliente la ofrece. Usá el mismo prefijo en todos los comandos para agrupar la actividad. [Captura y cierre de medición](MEDICION.md)

## 1. Indexar y priorizar

```sh
python v10/00-creacion-segundo-cerebro/scripts/mapear.py procesar --id ID_CORRIDA-mapa --repo "REPO_LOCAL" --app "APLICACION" --rev "REVISION"
```

Agregá `--modulos RUTA` si hay una agrupación acordada y `--anterior ENTREGA_ANTERIOR` si hay una entrega para reutilizar. El script examina el commit local y devuelve la ruta de la entrega. Conservá las omisiones en el informe. Para decidir qué mirar, leé el resultado acotado de este comando.

```sh
python v10/00-creacion-segundo-cerebro/scripts/navegar.py procesar --id ID_CORRIDA-mapa-breve --mapa "MAPA" --resumen
```

`--modulo ID` lista los archivos y símbolos de un módulo. Para continuar una lista usá `--desplazamiento N`. Al actualizar una entrega, priorizá los módulos marcados `pendiente`.

## 2. Buscar evidencia y completar fichas

Buscá contratos, puntos de entrada, pruebas y reglas por módulo. Usá términos concretos del mapa o del alcance. Agrupá consultas relacionadas en una llamada y empezá con un presupuesto chico. Leé solo el `contexto.json` publicado por cada llamada.

```sh
python v10/00-creacion-segundo-cerebro/scripts/navegar.py procesar --id ID_CORRIDA-busqueda-01 --mapa "MAPA" --modulo "MODULO" --consulta "regla o símbolo" --consulta "término relacionado" --max-chars 4500
python v10/00-creacion-segundo-cerebro/scripts/navegar.py procesar --id ID_CORRIDA-detalle-01 --mapa "MAPA" --rango "ARCHIVO" DESDE HASTA --max-chars 2400
```

Usá el rango exacto si una búsqueda marca líneas recortadas o la decisión necesita contexto. Copiá `borradores/ID-MODULO.json` a una ruta de trabajo y completalo según el [formato](FORMATO.md). Guardá una afirmación comprobable por concepto, con actor o condición y resultado cuando corresponda. Agregá `relaciones` si la evidencia sustenta un vínculo con otro concepto. Una prueba que enuncia el resultado sirve como evidencia de lo que se espera. Separá los comportamientos que dependen del entorno y las reglas todavía desconocidas en `pendientes`. Si el mapa basta para continuar, pasá al siguiente módulo.

## 3. Publicar y pasar a análisis

```sh
python v10/00-creacion-segundo-cerebro/scripts/publicar.py procesar --id ID_CORRIDA-publicar --mapa "MAPA" --revision "FICHA.json"
```

Repetí `--revision` para agregar fichas. Pasá el mismo `--anterior` usado al preparar una actualización. El script valida los localizadores y genera el bundle OKF 0.2 en `corpus/` con índices, conceptos y enlaces. Revisá `manifiesto.json` para ubicar los vínculos pendientes. Corregí las referencias que fallen y publicá con otro ID. Si queda cobertura parcial, conservá la entrega con sus pendientes. Para la etapa 01, entregá la carpeta publicada completa.

## 4. Medir y verificar la recuperación

Registrá el corte con `publicar.py medir` cuando el exportador haya escrito el último turno. Si la conversación sigue activa, registrá un corte final después de cerrarla. Ejecutá `diagnosticar.py` para verificar estructura y recuperación bajo el presupuesto de la etapa 01. Si QA proporcionó `PRUEBAS_RECUPERACION`, pasalo con `--pruebas`.

```sh
python v10/00-creacion-segundo-cerebro/scripts/publicar.py medir --id ID_CORRIDA-publicar --archivo "TELEMETRIA_NATIVA"
python v10/00-creacion-segundo-cerebro/scripts/diagnosticar.py procesar --id ID_CORRIDA-diagnostico --corrida ID_CORRIDA --cerebro "ENTREGA_CEREBRO"
```

Entregá `diagnostico.json` y `diagnostico.md` junto con la ruta del bundle. El `logs/ID_CORRIDA-diagnostico/log00.md` reúne los dos archivos y la actividad de la corrida. Para un log detallado local, consolidá los IDs realmente usados.

```sh
python v10/00-creacion-segundo-cerebro/scripts/publicar.py consolidar --id ID_CORRIDA-mapa --id ID_CORRIDA-mapa-breve --id ID_CORRIDA-busqueda-01 --id ID_CORRIDA-publicar --id ID_CORRIDA-diagnostico
```
