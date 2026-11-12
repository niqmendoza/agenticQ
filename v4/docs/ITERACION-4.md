# Cuarta iteración del framework de QA

Las sesiones nuevas con `--profile` usan el contrato `qa-run/2`. El CLI y el motor documental están en `v4/`. Las sesiones previas siguen leyendo su esquema anterior. El perfil se prepara a partir del alcance aprobado y se copia en `run.json`. Usá la configuración de un entorno de pruebas y fixtures sintéticos o sanitizados.

```sh
python3 src/qa.py openapi --spec /ruta/openapi.json
python3 src/qa.py init --profile examples/perfil-iteracion4.json --run /tmp/qa-iteracion4 --title 'QA API'
python3 src/qa.py record --run /tmp/qa-iteracion4 --json examples/casos-iteracion4.json
python3 src/qa.py execute --run /tmp/qa-iteracion4 --case API-01 --via http
python3 src/qa.py execute --run /tmp/qa-iteracion4 --case UI-01 --via playwright
```

Adaptá ambos ejemplos antes de ejecutarlos. `--corpus` permite sumar las consultas al segundo cerebro y es opcional con perfil. `openapi` inventaría operaciones desde OpenAPI o Swagger en JSON local. El perfil indica qué operaciones concretas se van a probar. El inventario no dispara peticiones. La versión actual no resuelve referencias externas, YAML ni esquemas de respuesta automáticamente.

## Canales de prueba

Los [recorridos variables y casos negativos](PRUEBAS-EXPLORATORIAS.md) agregan variaciones reproducibles de interfaz y fixtures de tipo incorrecto.

- **HTTP directo.** Declarar `http.method` y `http.path` en el caso. Deben coincidir con una operación del perfil. Se puede usar una ruta con query explícita, `--body` con un fixture JSON y `authenticated: true` con una variable `bearer_env` configurada. El runner comprueba estado, tipo de contenido o igualdad de un valor JSON. Registra las aserciones, estado HTTP y tipo de contenido. La evidencia no guarda el cuerpo ni las credenciales. Los códigos de salida de `execute` son 0 aprobado, 1 fallido, 2 configuración inválida y 3 bloqueado.
- **Playwright sobre Swagger u otra UI.** Instalar Playwright para Python y Chromium en el entorno del runner. El perfil admite `browser_channel: "chrome"` si Chrome ya está instalado. Declarar `browser_path` y usar criterios de estado HTTP y texto visible. Este smoke comprueba que la UI de documentación abre y expone la operación. Por defecto carga recursos del mismo origen. Si Swagger depende de un CDN, declarar las URLs HTTPS exactas de sus scripts y hojas de estilo en `browser_assets`. Para interacciones como expandir operaciones o usar *Try it out* en el entorno de pruebas, ejecutar el flujo con el Playwright del agente y registrar los resultados por criterio con `execution_method: "playwright"`. Para comprobar el contrato de la API usar una prueba HTTP separada.
- **MCP de base de datos.** Conectar el MCP en el agente anfitrión y declarar en `db_sources` el identificador del servidor y herramienta aprobada. Usar un rol de solo lectura y una vista o conjunto de datos de QA. Consultar un fixture conocido, un conteo o una proyección necesaria para el criterio. Guardar una evidencia sanitizada con referencia de herramienta, entorno, resultado mínimo y hora. Registrar con `record`, `execution_method: "mcp_db"` y `db_source` igual al identificador declarado. El CLI registra y valida ese resultado. El [MCP PostgreSQL independiente](../../tools/postgres-mcp/README.md) incluye sondas y un puente reproducible para PappU. El agente invoca el MCP mediante su conexión. Si la herramienta no está conectada, registrar el criterio como bloqueado con el motivo.

## Preparación y lotes para Copilot

- `preflight --run RUTA` verifica las operaciones GET marcadas `probe: true` y escribe `preflight.json`. Retorna 3 si una sonda no entrega 200 JSON. Detecta disponibilidad del paquete Playwright y de la variable de autenticación cuando está declarada. El agente anfitrión comprueba por separado conexión MCP y contadores de tokens.
- `freeze-plan --run RUTA` conserva el CSV inicial antes del primer intento. Para una nueva corrida del mismo plan, usar otra sesión.
- `suite --run RUTA --manifest ARCHIVO` ejecuta los casos HTTP y Playwright seleccionados en un manifiesto JSON. Cada entrada indica `case`, `via` y, si corresponde, `body` relativo al manifiesto. Conserva los intentos y escribe `suite.json` con el último lote, más una copia del resultado de cada lote bajo `artifacts/`. Los resultados por caso siguen en los CSV y la bitácora.

## Trazabilidad de la corrida

Antes de crear casos, ejecutar `preflight --run RUTA` y registrar una nota de preparación con versión, flags, disponibilidad de Swagger/HTTP/MCP, roles, datos de prueba y fuentes de telemetría disponibles. Hacerlo al comienzo permite identificar los bloqueos del entorno sin cambiar la prioridad o los pasos de los casos. Preparar credenciales de QA antes de la corrida, mediante el mecanismo del entorno. Registrar la limpieza de fixtures cuando corresponda.

Cada caso requiere `requirement`, pasos y una lista `criteria` con `id` y `expected`. Para oráculos documentados, usar referencias estructuradas con `path` y `locator` o `start/end`. Para oráculos pendientes, registrar `oracle_pending_reason`. El requisito debería ser estable. Si no tiene ID en la fuente, crear uno local y vincularlo a la referencia.

Cada ejecución externa se registra con el siguiente formato. El archivo de evidencia debe existir dentro de la sesión para cualquier criterio aprobado o fallido.

```json
{
  "kind": "execution",
  "case_id": "DB-01",
  "status": "partial",
  "execution_method": "mcp_db",
  "db_source": "qa-db.read_fixture_summary",
  "started_at": "2026-11-12T13:00:00Z",
  "finished_at": "2026-11-12T13:00:01Z",
  "duration_ms": 1000,
  "observation": "Se verificó el conteo. Falta un dato del fixture.",
  "evidence": "evidencias/DB-01.json",
  "results": [
    {"id": "conteo", "status": "passed", "observation": "Coincide el conteo.", "evidence": "evidencias/DB-01.json"},
    {"id": "estado", "status": "blocked", "observation": "La vista de QA no expone el estado."}
  ]
}
```

Todos los criterios deben aparecer una vez. Si alguno falla, el caso falla. Si todos pasan, el caso pasa. Si hay aprobados y otros bloqueados o pendientes de ejecución, el caso queda `partial`. Si ninguno se verificó, queda `blocked` o `not_run` según los resultados registrados. La validación comprueba estructura, referencia y estado derivado. La calidad de la aserción y el contenido de la evidencia siguen sujetos a revisión.

`casos.csv`, `ejecuciones.csv` y `requisitos.csv` se regeneran con `report`. El último enumera los requisitos registrados y sus casos. Para calcular cobertura total hace falta un catálogo independiente de requisitos del alcance. Las horas observadas y la duración de pruebas externas deben proceder de la ejecución. La hora del registro se conserva aparte. Seguir la [guía de tokens](MEDICION-TOKENS.md) y reportar los contadores nativos solamente cuando el agente los pueda observar.

Al cierre ejecutar `audit --run RUTA --requirements CATALOGO.json`. El catálogo opcional es una lista independiente de IDs. La auditoría revisa el último intento y sus archivos, identifica casos inferidos y requisitos sin casos. Si falta evidencia referenciada, marca el caso como `invalid_evidence` en `audit.json` y devuelve código 1.
