# RAGFlow local · prueba por API

Primera etapa completada: RAGFlow en Docker, el mismo segundo cerebro del ensayo anterior y recuperación por API. Después se agregó un primer adaptador de contexto compacto; la generación de casos todavía no se ejecutó.

La primera comprobación quedó completada: cinco servicios saludables, API y web respondiendo, 80 documentos procesados y 143 fragmentos indexados. Una consulta del ensayo anterior devolvió cinco fragmentos de fuentes identificadas. Ver [resultado de la comprobación](RESULTADO.md).

## Entorno

- Proyecto Compose independiente: `qa-ragflow-local`.
- RAGFlow Python `v0.27.3`, imagen `linux/amd64`; en Apple Silicon se ejecuta con emulación de Docker Desktop. No se presenta como una instalación nativa ARM.
- Dependencias: Elasticsearch 8.11.3, MySQL 8.0.40, almacenamiento compatible MinIO y Valkey. Cada servicio tiene un volumen propio del proyecto.
- Interfaz: <http://127.0.0.1:8088>. API: <http://127.0.0.1:9388>.
- Sólo se publican la interfaz y la API en loopback. Las bases de datos no tienen puertos publicados.
- Embeddings: Ollama que ya está instalado en esta Mac, con `nomic-embed-text:latest`. Desde el contenedor se accede mediante `http://host.docker.internal:11434`.
- No se configura un modelo generativo ni un proveedor externo. La consulta usa `/api/v1/retrieval`.

Las contraseñas de los servicios se generaron en `.env` (permisos 600). La cuenta de prueba y su API key se guardan en `state/credentials.local.json`, también con permisos 600. No compartir esos archivos.

Para entrar a la interfaz, usar el correo y la contraseña de esa cuenta de prueba. `connection.json` contiene la URL y el dataset para los scripts; no contiene la API key.

Durante esta instalación se amplió el límite del disco virtual de Docker Desktop de 32 a 48 GiB porque estaba lleno. No se eliminaron imágenes, contenedores ni volúmenes de otros proyectos. Las cinco imágenes efectivamente usadas, sus arquitecturas y digests están en `images.lock.json`.

## Arranque y carga

Desde esta carpeta, en una copia nueva del repositorio, generar primero un `.env` privado. Si ya existe, conservarlo para no cambiar las claves de los volúmenes actuales:

```sh
python3 - <<'PYENV'
from pathlib import Path
import os, secrets
path = Path('.env')
if path.exists():
    print('.env existente conservado.')
else:
    text = Path('.env.example').read_text()
    for key in ('MYSQL_PASSWORD', 'ELASTIC_PASSWORD', 'MINIO_PASSWORD', 'REDIS_PASSWORD'):
        text = text.replace('CHANGE_ME_' + key, secrets.token_urlsafe(24))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as out:
        out.write(text)
    print('.env privado creado.')
PYENV
```

Luego:

```sh
python3 manage.py start
python3 manage.py status
python3 setup_api.py
python3 check_api.py
```

`setup_api.py` requiere que la API ya responda. Crea una cuenta de prueba local, configura el proveedor de embeddings, crea el dataset, carga los documentos y solicita su procesamiento. Conserva los documentos cargados en `state/corpus.local.json` para poder continuar una carga interrumpida. No reemplaza documentos que hayan cambiado ni borra datasets anteriores.

La fuente predeterminada es `../../Post Harness/evidencias/fuentes`. Antes de cargar, verifica los 80 archivos contra los SHA-256 del inventario del ensayo. La copia congelada coincide con el corpus utilizado para medir los scripts; no se altera el segundo cerebro original.

La carga de archivos y la indexación son pasos distintos. `check_api.py` muestra cuántos documentos reconoce la API, sus estados y la cantidad de fragmentos. Se considera lista la prueba cuando el procesamiento termina y una consulta devuelve evidencia pertinente.

## Consulta por API

```sh
python3 check_api.py --question '¿Cómo se controla el acceso a los recursos?'
```

El cliente está en `../scripts/ragflow_client.py`. Limita la búsqueda al dataset configurado y solicita cinco fragmentos por consulta. `check_api.py` conserva los campos nativos de RAGFlow para diagnóstico; el nuevo adaptador `../scripts/retrieve.py` implementa por separado el contrato de contexto `qa-context/1`. Las credenciales no se incluyen en los resultados ni en las solicitudes registradas por los tests.

Para guardar una evidencia de consulta:

```sh
python3 check_api.py --question '¿Cómo se controla el acceso a los recursos?' --save state/consulta.local.json
```

Esto comprueba conectividad y recuperación. No mide por sí solo el ahorro de tokens de Copilot ni demuestra cobertura funcional completa.

## Operación

```sh
python3 manage.py logs
python3 manage.py stop
```

`stop` conserva los volúmenes para el próximo arranque. Ningún script ejecuta limpiezas globales de Docker.

## Procedencia y verificaciones

`upstream/` conserva archivos públicos oficiales de la release (incluidos su `.env` de referencia y la clave RSA **pública** usada para el login; ninguno contiene las credenciales generadas de esta instalación) y `upstream-manifest.json` registra sus URLs y hashes. `compose.json` adapta puertos, límites de memoria y dependencias al piloto local. El núcleo `brain.py` y las evidencias históricas de Post Harness se mantienen como referencia medida.

Pruebas del cliente HTTP y regresión del modo local:

```sh
cd ..
"../Post Harness/.venv/bin/python" -m unittest discover -s tests -v
```

Fuentes: [release de RAGFlow](https://github.com/infiniflow/ragflow/releases/tag/v0.27.3), [configuración oficial de Docker en esa release](https://github.com/infiniflow/ragflow/tree/v0.27.3/docker), [API HTTP de esa release](https://github.com/infiniflow/ragflow/blob/v0.27.3/docs/references/http_api_reference.md).

## Pruebas de recuperación · 29 de octubre

[Abrir el reporte HTML autónomo](Pruebas-RAGFlow.html) o consultar [el informe Markdown](Pruebas-RAGFlow.md).

Se compararon las cinco consultas del ensayo anterior con 5 y 10 fragmentos de RAGFlow, el paquete inicial de los scripts locales y ampliaciones dirigidas. También se probaron repetición, autenticación inválida, dataset inexistente, servicio no disponible y cuatro consultas ajenas al dominio. La configuración de conexión sigue en su valor inicial: aumentar el umbral no resolvió la relevancia sin perder información pertinente.

Los resultados conservan respuestas nativas y un protocolo previo de 14 señales documentales. La cantidad de señales no equivale a cobertura exhaustiva ni a pruebas ejecutadas sobre la aplicación. Se cuentan tokens del texto devuelto con `o200k_base` como proxy; todavía no se midió el consumo real de Copilot.

Para repetir con nuevas carpetas de evidencia, desde `Post Harness V2`:

```sh
"../Post Harness/.venv/bin/python" ragflow-local/evaluate_retrieval.py --out ragflow-local/pruebas/NUEVA-EJECUCION
"../Post Harness/.venv/bin/python" ragflow-local/calibrate_retrieval.py --out ragflow-local/pruebas/NUEVA-CALIBRACION
python3 ragflow-local/build_test_report.py --initial ragflow-local/pruebas/NUEVA-EJECUCION --calibration ragflow-local/pruebas/NUEVA-CALIBRACION --out ragflow-local/NUEVO-REPORTE
```

Las carpetas iniciales y sus manifiestos de hashes están en `pruebas/2026-10-29-inicial` y `pruebas/2026-10-29-calibracion`. La regresión automatizada ahora comprende 27 tests aprobados.

## Adaptador de contexto compacto · piloto v1

La [guía del adaptador](../GUIA-CONTEXTO-RAGFLOW.md) explica el nuevo contrato, la consulta desde scripts y el uso posterior con Copilot. El [resultado del ensayo](RESULTADO-ADAPTADOR.md) conserva la comparación sobre tres preguntas nuevas del mismo corpus: 41,1% menos tokens proxy en la salida sin recorte, con los 13 fragmentos únicos preservados. Con presupuesto acotado se entregan pendientes explícitos y se pueden recuperar en otra lectura. La suite ampliada comprende 43 tests aprobados.

La relevancia sigue necesitando revisión: la consulta ajena al tema aún recibió resultados. No se cambió el modelo de embeddings ni se midió consumo real de Copilot.
