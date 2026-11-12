# Piloto local de V4 con PappU

El piloto usa los contenedores locales existentes y las rutas GET documentadas. El segundo cerebro utilizado fue `PAPU/docs/PappU`. El checkout de PappU estaba en `d6e4b02`. Las imágenes en ejecución no exponen una etiqueta de revisión que permita vincularlas a ese commit.

Se indexaron 44 documentos y 260 fragmentos. El paquete de tres consultas devolvió cinco pasajes de dos fuentes, con 37 elementos pendientes según el motor. Se amplió el tramo relevante de `backend-foundation.md` y se consultaron las definiciones de la API en el checkout. La especificación servida localmente tenía 65 rutas y 71 operaciones. Las cuatro pruebas funcionales seleccionadas cubrieron liveness, readiness, OpenAPI y el Swagger real. En la corrida de verificación pasaron 4/4 casos y 11/11 criterios. Los intentos HTTP duraron 12, 8 y 34 ms. El intento de Swagger con Chrome duró 7,447 s e incluye arranque del navegador y carga de recursos. Son tiempos de una sola corrida local. El piloto no mide cobertura del conjunto de 71 operaciones.

## Repetir desde la raíz del repositorio

Usar Python 3.10 o superior. Para el caso de Swagger, instalar Playwright en el intérprete elegido y disponer de Chrome o ajustar `browser_channel` al navegador instalado. El perfil de ejemplo usa el stack local en el puerto 8080 y declara los dos recursos de Swagger que carga la aplicación.

```sh
RUN="$PWD/v4/sessions/pappu-local-repeticion"
PAPPU_DOCS="$HOME/Desktop/Code/PAPU/docs/PappU"

python3 v4/src/qa.py init --profile v4/examples/pappu/perfil.json --run "$RUN" --corpus "$PAPPU_DOCS" --title "PappU local"
python3 v4/src/qa.py preflight --run "$RUN"
python3 v4/src/qa.py index --run "$RUN"
python3 v4/src/qa.py pack --run "$RUN" --queries v4/examples/pappu/consultas.json --max-chars 26000
python3 v4/src/qa.py show --run "$RUN" backend-foundation.md --start 80 --end 105 --replay
curl -fsS --max-time 10 http://127.0.0.1:8080/api/openapi.json -o "$RUN/artifacts/openapi-local.json"
python3 v4/src/qa.py openapi --spec "$RUN/artifacts/openapi-local.json" > "$RUN/artifacts/inventario-openapi.json"
python3 v4/src/qa.py record --run "$RUN" --json v4/examples/pappu/casos.json
python3 v4/src/qa.py freeze-plan --run "$RUN"
python3 v4/src/qa.py suite --run "$RUN" --manifest v4/examples/pappu/suite.json
```

La corrida conserva el plan, el resultado de cada criterio, el método, las horas y la duración. Los archivos del piloto son locales y `v4/sessions/` queda fuera de Git. Readiness verificó el resultado público de la sonda de la aplicación. El piloto posterior añadió una consulta real por el [MCP PostgreSQL](../../tools/postgres-mcp/README.md). Con el esquema `pappu`, la conexión confirmó solo lectura y devolvió una revisión Alembic. Pasaron 5/5 casos y 13/13 criterios en el piloto combinado, con los cinco requisitos seleccionados auditados y cero referencias de evidencia faltantes. Los contadores de tokens del agente tampoco estuvieron disponibles durante este piloto.

| Mejora | Herramienta | Proyección a comprobar |
| --- | --- | --- |
| Detectar dependencias antes de diseñar casos | `preflight`, perfil y nota de entorno | Menos casos bloqueados descubiertos tarde. Medir cuántos bloqueos detecta la preparación frente a la ejecución. |
| Vincular requisito, evidencia y esperado | Contrato por criterio y `requisitos.csv` | Menos aprobaciones con verificaciones faltantes. Auditar la proporción de aprobados respaldados por todos los criterios. |
| Preservar el plan y repetir un subconjunto | `freeze-plan`, `suite` y manifiesto | Menos comandos manuales y reintentos trazables. Comparar tiempo de preparación y número de intervenciones. |
| Separar contrato API y UI interactiva | `openapi`, runner HTTP y runner Playwright | Detectar desviaciones entre la respuesta HTTP y lo que muestra Swagger. Comparar resultados de ambos canales por operación seleccionada. |
| Registrar resultados persistidos | Evidencia por criterio mediante MCP de lectura en el agente | Verificar invariantes de datos con fixtures controlados. Requiere una conexión y una prueba real. |
| Medir operación y consumo | Duración por intento y plantilla de tokens por etapa | Comparar corridas equivalentes cuando se disponga de contadores. Medir porcentaje de etapas con telemetría. |


Para repetir el caso de base de datos, usar el [puente MCP](../../tools/postgres-mcp/README.md) después de ejecutar la suite y cerrar con:

```sh
python3 v4/src/qa.py audit --run "$RUN" --requirements v4/examples/pappu/requisitos.json
```

El catálogo del ejemplo corresponde al piloto. Para medir cobertura de una release, usar un catálogo definido fuera de la generación de casos.
