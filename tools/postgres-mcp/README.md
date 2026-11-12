# MCP PostgreSQL para QA

Servidor independiente de V4 que usa el [SDK oficial de MCP](https://github.com/modelcontextprotocol/python-sdk) y el transporte stdio. Expone dos herramientas con entradas vacías. `health` comprueba la conexión y el modo de transacción. `alembic_revisions` devuelve hasta diez identificadores de migración del esquema configurado. Las consultas son fijas, usan transacciones de solo lectura y tienen límites de tiempo. El modo Docker usa el rol configurado en el contenedor existente, que puede tener permisos más amplios que las sondas. Para un entorno compartido, configurar un servicio libpq y un rol de QA con permiso de lectura sobre la tabla requerida.

## Instalar y verificar en local

Desde la raíz del repositorio, con Python 3.11 o superior y el contenedor PostgreSQL de PAPPU corriendo:

```sh
python3 -m venv tools/postgres-mcp/.venv
tools/postgres-mcp/.venv/bin/python -m pip install -r tools/postgres-mcp/requirements.txt
tools/postgres-mcp/.venv/bin/python tools/postgres-mcp/probe.py \
  --docker pappu-local-current-postgres-1 --alembic-schema pappu
```

`probe.py` inicia el servidor, negocia el protocolo, lista las herramientas, las invoca y escribe JSON verificable en stdout. Para PostgreSQL sin Alembic, usar `--health-only`. Si el esquema no se declara, se usa `public`. La conexión alternativa usa `--service NOMBRE` y el binario `psql` local. Los archivos `PGSERVICEFILE` y `PGPASSFILE` pueden configurarse fuera del repositorio. No pasar claves como argumentos.

## Conectar a Copilot

En el agente anfitrión, agregar un servidor de tipo **Command (stdio)** con identificador `qa-postgres`. Usar la ruta absoluta a `tools/postgres-mcp/.venv/bin/python` como comando. Los argumentos son la ruta absoluta a `tools/postgres-mcp/server.py`, `--docker`, `pappu-local-current-postgres-1`, `--alembic-schema` y `pappu`. El host debe tener acceso a Docker. Para verificar el registro, pedir que invoque `health` y revisar la llamada en el chat. [Configuración MCP en VS Code](https://code.visualstudio.com/docs/agent-customization/mcp-servers).

## Registrar en una sesión V4

La sesión debe declarar `qa-postgres.health+alembic_revisions` en `db_sources` y tener un caso con los criterios `connection` y `migration_revision`. El puente guarda evidencia y registra el intento en el CLI existente. Usar el caso de ejemplo de PAPPU para probar conectividad y la presencia de una revisión. Una revisión existente no demuestra que coincida con una release objetivo.

```sh
tools/postgres-mcp/.venv/bin/python tools/postgres-mcp/record_v4.py \
  --docker pappu-local-current-postgres-1 --alembic-schema pappu \
  --qa-cli v4/src/qa.py --run "$RUN" --case PAPPU-POSTGRES
```
