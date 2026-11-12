"""Ejecuta las sondas PostgreSQL por MCP y emite evidencia JSON sanitizada."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import sys
from time import perf_counter

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def read_tools(mode, target, health_only=False, alembic_schema="public"):
    parameters = StdioServerParameters(
        command=sys.executable,
        env={
            key: os.environ[key]
            for key in ("PGSERVICEFILE", "PGPASSFILE", "PGSYSCONFDIR")
            if key in os.environ
        },
        args=[
            str(Path(__file__).with_name("server.py")),
            mode,
            target,
            "--alembic-schema",
            alembic_schema,
        ],
    )
    async with stdio_client(parameters) as (read, write), ClientSession(
        read, write
    ) as session:
        await session.initialize()
        available = {tool.name for tool in (await session.list_tools()).tools}
        if available != {"health", "alembic_revisions"}:
            raise ValueError(
                "El servidor MCP devolvió un inventario distinto del esperado."
            )
        output = {}
        for name in ("health",) if health_only else ("health", "alembic_revisions"):
            started = perf_counter()
            result = await session.call_tool(name, {})
            content = result.structuredContent
            if result.isError or not isinstance(content, dict):
                output[name] = {
                    "error": "La herramienta no devolvió evidencia verificable.",
                    "duration_ms": round((perf_counter() - started) * 1000),
                }
                continue
            if name == "health":
                if content != {"connected": True, "read_only": True}:
                    raise ValueError("Respuesta de salud inválida.")
                observed = {"connected": True, "read_only": True}
            else:
                revisions = content.get("revisions")
                if (
                    not isinstance(revisions, list)
                    or len(revisions) > 10
                    or not all(
                        isinstance(value, str)
                        and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value)
                        for value in revisions
                    )
                    or content.get("count") != len(revisions)
                ):
                    raise ValueError("Respuesta de migraciones inválida.")
                observed = {"revisions": revisions, "count": len(revisions)}
            output[name] = {
                **observed,
                "duration_ms": round((perf_counter() - started) * 1000),
            }
        return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--docker")
    mode.add_argument("--service")
    parser.add_argument("--health-only", action="store_true")
    parser.add_argument("--alembic-schema", default="public")
    args = parser.parse_args()
    try:
        evidence = asyncio.run(
            asyncio.wait_for(
                read_tools(
                    "--docker" if args.docker else "--service",
                    args.docker or args.service,
                    args.health_only,
                    alembic_schema=args.alembic_schema,
                ),
                timeout=30,
            )
        )
    except (ExceptionGroup, OSError, ValueError, TimeoutError):
        print("La verificación MCP PostgreSQL no se completó.", file=sys.stderr)
        return 1
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 1 if any("error" in tool for tool in evidence.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
