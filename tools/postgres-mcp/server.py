"""MCP stdio con consultas PostgreSQL predefinidas para QA."""

import argparse
import re
import subprocess
from typing import TypedDict

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


PSQL = ["psql", "-X", "-qAt", "--no-password", "-v", "ON_ERROR_STOP=1"]
CONTAINER_COMMAND = 'exec psql -X -qAt --no-password -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "${POSTGRES_DB:-$POSTGRES_USER}"'
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, openWorldHint=False
)


class Health(TypedDict):
    connected: bool
    read_only: bool


class Revisions(TypedDict):
    revisions: list[str]
    count: int


def execute_probe(command, sql):
    script = (
        f"BEGIN READ ONLY;\nSET LOCAL statement_timeout = '3s';\n{sql}\nROLLBACK;\n"
    )
    try:
        result = subprocess.run(
            command, input=script, capture_output=True, text=True, timeout=8, check=True
        )
    except (OSError, subprocess.SubprocessError):
        raise RuntimeError("La consulta PostgreSQL no se completó.") from None
    return result.stdout.splitlines()


def make_server(command, alembic_schema):
    server = FastMCP("qa-postgres")

    @server.tool(annotations=READ_ONLY)
    def health() -> Health:
        """Confirma conectividad y una transacción de solo lectura."""
        rows = execute_probe(
            command, "SELECT 1, current_setting('transaction_read_only');"
        )
        if rows != ["1|on"]:
            raise RuntimeError("La sonda devolvió un resultado inesperado.")
        return {"connected": True, "read_only": True}

    @server.tool(annotations=READ_ONLY)
    def alembic_revisions() -> Revisions:
        """Obtiene identificadores de migración desde la tabla Alembic del esquema configurado."""
        rows = execute_probe(
            command,
            f'SELECT version_num FROM "{alembic_schema}".alembic_version ORDER BY version_num LIMIT 11;',
        )
        if len(rows) > 10 or any(
            not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", row) for row in rows
        ):
            raise RuntimeError(
                "El estado de migraciones no coincide con el formato esperado."
            )
        return {"revisions": rows, "count": len(rows)}

    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--docker", metavar="CONTAINER", help="Contenedor local con psql."
    )
    mode.add_argument("--service", help="Servicio libpq configurado con un rol de QA.")
    parser.add_argument("--alembic-schema", default="public")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", args.alembic_schema):
        parser.error("Nombre de esquema inválido.")
    if args.docker:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.docker):
            parser.error("Nombre de contenedor inválido.")
        command = ["docker", "exec", "-i", args.docker, "sh", "-c", CONTAINER_COMMAND]
    else:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.service):
            parser.error("Nombre de servicio libpq inválido.")
        command = [*PSQL, "-d", f"service={args.service}"]
    make_server(command, args.alembic_schema).run(transport="stdio")


if __name__ == "__main__":
    main()
