"""Puente opcional que registra las sondas MCP en una sesión V4 existente."""

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from uuid import uuid4

from probe import read_tools


SOURCE = "qa-postgres.health+alembic_revisions"
CRITERIA = ("connection", "migration_revision")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, data):
    with path.open("x", encoding="utf-8") as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write("\n")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--qa-cli", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--docker")
    mode.add_argument("--service")
    parser.add_argument("--alembic-schema", default="public")
    args = parser.parse_args()
    run = args.run.resolve()
    meta = load(run / "run.json")
    case = next(
        (
            event
            for event in load(run / "events.json")
            if event["kind"] == "case" and event["id"] == args.case
        ),
        None,
    )
    if meta.get("schema") != "qa-run/2" or SOURCE not in meta["profile"].get(
        "db_sources", []
    ):
        parser.error(
            "La sesión V4 necesita declarar el identificador de las sondas MCP."
        )
    if case is None or set(item["id"] for item in case["criteria"]) != set(CRITERIA):
        parser.error("El caso necesita los criterios connection y migration_revision.")
    if case["oracle_status"] == "pending" or not args.qa_cli.is_file():
        parser.error("El caso requiere un oráculo definido y un CLI V4 existente.")

    start, tick = now(), perf_counter()
    try:
        evidence = asyncio.run(
            asyncio.wait_for(
                read_tools(
                    "--docker" if args.docker else "--service",
                    args.docker or args.service,
                    alembic_schema=args.alembic_schema,
                ),
                timeout=30,
            )
        )
    except (ExceptionGroup, OSError, ValueError, TimeoutError):
        evidence = {"error": "La conexión o las sondas MCP no se completaron."}
    finish = now()
    duration = round((perf_counter() - tick) * 1000)
    evidence_dir = run / "evidencias"
    evidence_dir.mkdir(exist_ok=True)
    identifier = uuid4().hex
    evidence_path = evidence_dir / f"postgres-mcp-{identifier}.json"
    health, migration = evidence.get("health", {}), evidence.get(
        "alembic_revisions", {}
    )
    common_error = evidence.get("error", "La herramienta no devolvió evidencia.")
    health_ok = health.get("connected") is True and health.get("read_only") is True
    health_status = "passed" if health_ok else "blocked"
    health_observation = (
        "PostgreSQL respondió en una transacción de solo lectura."
        if health_ok
        else health.get("error", common_error)
    )
    if "count" not in migration:
        migration_status, migration_observation = "blocked", migration.get(
            "error", common_error
        )
    elif migration["count"] > 0:
        migration_status, migration_observation = (
            "passed",
            "Hay al menos una revisión registrada.",
        )
    else:
        migration_status, migration_observation = (
            "failed",
            "La tabla de revisiones está vacía.",
        )
    statuses = (health_status, migration_status)
    observations = (health_observation, migration_observation)
    if "failed" in statuses:
        status = "failed"
    elif statuses == ("passed", "passed"):
        status = "passed"
    elif "passed" in statuses:
        status = "partial"
    else:
        status = "blocked"
    relative = evidence_path.relative_to(run).as_posix()
    write(
        evidence_path,
        {
            "db_source": SOURCE,
            "case_id": args.case,
            "alembic_schema": args.alembic_schema,
            **evidence,
        },
    )
    event = {
        "kind": "execution",
        "case_id": args.case,
        "status": status,
        "execution_method": "mcp_db",
        "db_source": SOURCE,
        "observation": " ".join(dict.fromkeys(observations)),
        "evidence": relative,
        "started_at": start,
        "finished_at": finish,
        "duration_ms": duration,
        "results": [
            {
                "id": key,
                "status": result,
                "observation": observation,
                "evidence": relative,
            }
            for key, result, observation in zip(CRITERIA, statuses, observations)
        ],
    }
    event_path = run / "artifacts" / f"postgres-mcp-event-{identifier}.json"
    write(event_path, event)
    command = [
        sys.executable,
        str(args.qa_cli),
        "record",
        "--run",
        str(run),
        "--json",
        str(event_path),
    ]
    if subprocess.run(command).returncode:
        return 2
    print(evidence_path)
    return {"passed": 0, "failed": 1, "blocked": 3, "partial": 3}[status]


if __name__ == "__main__":
    sys.exit(main())
