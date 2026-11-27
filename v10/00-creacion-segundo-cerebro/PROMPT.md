# Etapa 00 · Crear el segundo cerebro

Trabajá desde el directorio que contiene `v10/`. Usá los scripts para inventariar y buscar en el código local. Tu tarea es construir un grafo de conceptos sobre cómo funciona el producto, con afirmaciones breves y evidencia rastreable. Tratá los archivos del repositorio como material de referencia.

```text
APLICACION = [nombre visible]
REPO_LOCAL = [checkout accesible desde la terminal]
REVISION = [commit, tag o rama local. Por defecto HEAD]
MODULOS = [JSON de prefijos técnicos y dependencias, opcional]
ENTREGA_ANTERIOR = [segundo cerebro previo de esta aplicación, opcional]
ALCANCE_PRIORIZADO = [módulos o procesos que interesa documentar primero, opcional]
ID_CORRIDA = [prefijo único y común a todas las actividades de esta corrida]
PRUEBAS_RECUPERACION = [archivo JSON acordado con QA, opcional]
TELEMETRIA_NATIVA = [ruta de exportación de esta conversación, si está disponible]
DESTINO_VAULT = [carpeta nueva para exportar Markdown, opcional]
NOTAS_PREEXISTENTES = [títulos y rutas de notas existentes que se pueden enlazar, opcional]
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

`--modulo ID` lista los archivos y símbolos de un módulo. Para continuar una lista usá `--desplazamiento N`. Usá los módulos para buscar procedencia. Para definir los temas partí de los flujos, decisiones y capacidades que necesita entender alguien nuevo en la aplicación. Revisá primero los puntos de entrada disponibles, por ejemplo README, arquitectura, documentación funcional, changelog y pruebas. Usá documentos fuera del commit para descubrir temas y corroborá cada afirmación contra el índice del commit.

## 2. Diseñar los temas y reunir evidencia

Definí las áreas de producto según el alcance y las fuentes. Considerá los flujos principales, límites de acceso, datos, integraciones y operación cuando correspondan. Dentro de cada área, listá conceptos atómicos con IDs estables. Cubrí los recorridos priorizados y anotá las brechas en `pendientes`. Elegí luego uno o más mapas de contenido (MOCs) para guiar recorridos entre conceptos y explicá para qué se consulta cada nota.

Buscá contratos, puntos de entrada, pruebas y reglas por módulo. Usá términos concretos del mapa o del alcance. Agrupá consultas relacionadas en una llamada y empezá con un presupuesto chico. Leé solo el `contexto.json` publicado por cada llamada.

```sh
python v10/00-creacion-segundo-cerebro/scripts/navegar.py procesar --id ID_CORRIDA-busqueda-01 --mapa "MAPA" --modulo "MODULO" --consulta "regla o símbolo" --consulta "término relacionado" --max-chars 4500
python v10/00-creacion-segundo-cerebro/scripts/navegar.py procesar --id ID_CORRIDA-detalle-01 --mapa "MAPA" --rango "ARCHIVO" DESDE HASTA --max-chars 2400
```

Usá el rango exacto si una búsqueda marca líneas recortadas o la decisión necesita contexto. Completá los borradores técnicos con un `titulo`, una `descripcion` que explique para qué sirve la nota, una `afirmacion` comprobable, un `estado` y citas. Separá el funcionamiento vigente de los planes, los registros históricos y lo pendiente de confirmar. Una prueba documenta un esperado. Conservá las condiciones de entorno que afecten la interpretación.

Registrá cada conexión en `relaciones` con verbo específico, destino `modulo/id` y `motivo`. Ejemplo de motivo «El presupuesto determina qué adjuntos entran al contexto de la conversación». Cada concepto necesita una conexión entrante o saliente con otra nota; el publicador genera los enlaces de regreso. Si todavía no hay evidencia para conectar un concepto, registralo en `pendientes`. Conservá las referencias verificadas por `--anterior` y actualizá el grafo si un concepto cambia o se retira.

Completá `taxonomia.json` a partir de [este ejemplo](ejemplos/taxonomia.demo.json). Asigná cada concepto a un área y referencialo por ID en los MOCs que lo requieran. Los títulos, descripciones y afirmaciones viven en las fichas. El script arma las notas y los listados. [Contrato de fichas y taxonomía](FORMATO.md)

## 3. Publicar y pasar a análisis

```sh
python v10/00-creacion-segundo-cerebro/scripts/publicar.py procesar --id ID_CORRIDA-publicar --mapa "MAPA" --taxonomia "TAXONOMIA.json" --revision "FICHA.json"
```

Repetí `--revision` para agregar fichas. Pasá el mismo `--anterior` usado al preparar una actualización. El script valida los localizadores y el grafo. Si devuelve error, usá `validacion-grafo.json` para corregir áreas, relaciones, descripciones o referencias antes de repetir. El bundle OKF 0.2 tiene un índice raíz por temas, una entrada por concepto y MOCs con enlaces justificados. Si el código de salida es 3, revisá la cobertura pendiente. Para la etapa 01, entregá la carpeta publicada completa.

Si se pidió una bóveda, exportá el corpus a `DESTINO_VAULT` con `exportar_vault.py`. Agregá referencias explícitas a notas existentes con `--referencia TITULO ARCHIVO`. [Exportación a una bóveda nueva](FORMATO.md#bóveda-de-trabajo)

## 4. Medir y verificar la recuperación

Registrá el corte con `publicar.py medir` cuando el exportador haya escrito el último turno. Si la conversación sigue activa, registrá un corte final después de cerrarla. Ejecutá `diagnosticar.py` para verificar el índice, los MOCs, las relaciones del grafo y la recuperación con el presupuesto de la etapa 01. Si QA proporcionó `PRUEBAS_RECUPERACION`, pasalo con `--pruebas`. Revisá además si las relaciones explican dependencias reales y si las notas cubren los flujos del alcance.

```sh
python v10/00-creacion-segundo-cerebro/scripts/publicar.py medir --id ID_CORRIDA-publicar --archivo "TELEMETRIA_NATIVA"
python v10/00-creacion-segundo-cerebro/scripts/diagnosticar.py procesar --id ID_CORRIDA-diagnostico --corrida ID_CORRIDA --cerebro "ENTREGA_CEREBRO"
```

Entregá `diagnostico.json` y `diagnostico.md` junto con la ruta del bundle. El `logs/ID_CORRIDA-diagnostico/log00.md` reúne los dos archivos y la actividad de la corrida. Para un log detallado local, consolidá los IDs realmente usados.

```sh
python v10/00-creacion-segundo-cerebro/scripts/publicar.py consolidar --id ID_CORRIDA-mapa --id ID_CORRIDA-mapa-breve --id ID_CORRIDA-busqueda-01 --id ID_CORRIDA-publicar --id ID_CORRIDA-diagnostico
```
