#!/usr/bin/env python3
"""Operaciones reproducibles de una sesión de QA, sin ejecutar instrucciones del corpus."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ENGINE = Path(__file__).resolve().parent / "engine" / "brain.py"
from audit import audit
from json_tools import fixture_variant
from records import record
from runners import inventory, run_case, validate_profile
from session import append, load, read_json, render, timestamp, write_json
from workflow import freeze_plan, preflight, suite


def initialize(args):
    profile = read_json(args.profile) if args.profile else None
    if args.profile:
        validate_profile(profile)
    corpus = Path(args.corpus).resolve() if args.corpus else None
    run = Path(args.run).resolve()
    if (corpus is None and profile is None) or (
        corpus is not None and not corpus.is_dir()
    ):
        raise ValueError("El corpus debe ser un directorio existente.")
    if corpus is not None and (run == corpus or corpus in run.parents):
        raise ValueError("La sesión debe estar fuera del corpus.")
    run.mkdir(parents=True, exist_ok=False)
    (run / "artifacts").mkdir()
    write_json(
        run / "run.json",
        {
            "schema": "qa-run/2" if profile is not None else "qa-run/1",
            **({"profile": profile} if profile is not None else {}),
            "title": args.title,
            "corpus": str(corpus) if corpus else None,
            "started_utc": timestamp(),
        },
    )
    write_json(run / "events.json", [])
    append(
        run,
        {
            "kind": "note",
            "phase": "preparación",
            "observation": "Sesión creada; todavía no se indexó el corpus ni se ejecutaron pruebas.",
        },
    )
    print(run / "log.md")


def engine_operation(args):
    run, meta, _ = load(args.run)
    if not meta["corpus"]:
        raise ValueError("Esta sesión se creó sin corpus documental.")
    command = [
        sys.executable,
        str(ENGINE),
        "--db",
        str(run / "brain.sqlite"),
        "--session",
        str(run / "session.json"),
    ]
    if args.action == "index":
        command += ["index", meta["corpus"]]
    elif args.action == "pack":
        command += [
            "pack",
            "--queries-json",
            str(Path(args.queries).resolve()),
            "--max-chars",
            str(args.max_chars),
            "--max-lines",
            str(args.max_lines),
        ]
    elif args.action == "show":
        command += [
            "show",
            args.path,
            "--start",
            str(args.start),
            "--max-lines",
            str(args.max_lines),
            "--max-chars",
            str(args.max_chars),
        ]
        if args.end is not None:
            command += ["--end", str(args.end)]
        if args.replay:
            command.append("--replay")
    elif args.action in {"headings", "links"}:
        command += [args.action, args.path]
    else:
        command += ["verify", str(Path(args.result).resolve())]
        if args.requirements:
            command += ["--requirements-json", str(Path(args.requirements).resolve())]
    started = timestamp()
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    artifacts = run / "artifacts"
    sequence = (
        max(
            (
                int(path.name.split("-", 1)[0])
                for path in artifacts.glob("[0-9]*-*.json")
                if path.name.split("-", 1)[0].isdigit()
            ),
            default=0,
        )
        + 1
    )
    target = artifacts / f"{sequence:03d}-{args.action}.json"
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {
            "error": "El motor no devolvió JSON válido.",
            "stderr": result.stderr[:2000],
        }
        if result.returncode == 0:
            result.returncode = 2
    write_json(target, payload)
    event = {
        "kind": "note",
        "phase": args.action,
        "started_utc": started,
        "exit_code": result.returncode,
        "artifact": str(target.relative_to(run)),
        "arguments": command[5:],
        "observation": (
            "Operación completada."
            if result.returncode == 0
            else "Operación fallida; revisar artefacto."
        ),
    }
    if args.action == "pack" and result.returncode == 0:
        event.update(
            {
                "queries": payload.get("queries", []),
                "revision": payload.get("revision"),
                "sources": len(payload.get("sources", {})),
                "passages": len(payload.get("passages", [])),
                "pending_total": payload.get("pending_total"),
                "interpretation": "La recuperación no demuestra cobertura ni vigencia.",
            }
        )
    if args.action == "index" and result.returncode == 0:
        event["result"] = payload
    append(run, event)
    print(target)
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init", help="Crear una sesión nueva fuera del corpus")
    init.add_argument("--run", required=True)
    init.add_argument("--corpus")
    init.add_argument("--profile", help="Perfil JSON de la cuarta iteración")
    init.add_argument("--title", required=True)
    index = sub.add_parser("index", help="Indexar y registrar el resultado")
    index.add_argument("--run", required=True)
    pack = sub.add_parser("pack", help="Recuperar contexto y registrar límites")
    pack.add_argument("--run", required=True)
    pack.add_argument("--queries", required=True)
    pack.add_argument("--max-chars", type=int, default=50000)
    pack.add_argument("--max-lines", type=int, default=120)
    show = sub.add_parser("show", help="Ampliar un rango y registrar la lectura")
    show.add_argument("--run", required=True)
    show.add_argument("path")
    show.add_argument("--start", type=int, default=1)
    show.add_argument("--end", type=int)
    show.add_argument("--max-lines", type=int, default=120)
    show.add_argument("--max-chars", type=int, default=50000)
    show.add_argument("--replay", action="store_true")
    for action in ("headings", "links"):
        operation = sub.add_parser(action)
        operation.add_argument("--run", required=True)
        operation.add_argument("path")
    verify = sub.add_parser("verify", help="Verificar estructura y citas del motor V2")
    verify.add_argument("--run", required=True)
    verify.add_argument("--result", required=True)
    verify.add_argument("--requirements")
    event = sub.add_parser(
        "record", help="Registrar un caso, intento, hallazgo o nota JSON"
    )
    event.add_argument("--run", required=True)
    event.add_argument("--json", required=True)
    report = sub.add_parser("report", help="Regenerar log.md desde los eventos")
    report.add_argument("--run", required=True)
    execute = sub.add_parser("execute", help="Ejecutar un caso funcional del perfil")
    execute.add_argument("--run", required=True)
    execute.add_argument("--case", required=True)
    execute.add_argument("--via", choices=("http", "playwright"), required=True)
    execute.add_argument("--body", help="Fixture JSON para la petición HTTP")
    execute.add_argument(
        "--seed", type=int, help="Semilla alternativa para un recorrido Playwright"
    )
    openapi = sub.add_parser(
        "openapi", help="Inventariar operaciones de una especificación JSON"
    )
    openapi.add_argument("--spec", required=True)
    for name, handler in (
        ("preflight", preflight),
        ("freeze-plan", freeze_plan),
        ("suite", suite),
    ):
        command = sub.add_parser(name)
        command.add_argument("--run", required=True)
        command.set_defaults(workflow_handler=handler)
        if name == "suite":
            command.add_argument("--manifest", required=True)
    audit_parser = sub.add_parser(
        "audit", help="Revisar trazabilidad y evidencia del último intento"
    )
    audit_parser.add_argument("--run", required=True)
    audit_parser.add_argument(
        "--requirements", help="JSON con los IDs del catálogo acordado"
    )
    audit_parser.set_defaults(workflow_handler=audit)
    variant = sub.add_parser(
        "fixture-variant", help="Cambiar el tipo de un campo de un fixture JSON"
    )
    variant.add_argument("--fixture", required=True)
    variant.add_argument(
        "--path", required=True, help='Ruta JSON, por ejemplo ["name"]'
    )
    variant.add_argument("--value", required=True, help="Nuevo valor JSON")
    variant.add_argument("--out", required=True)
    variant.set_defaults(workflow_handler=fixture_variant)
    args = parser.parse_args()
    try:
        if hasattr(args, "workflow_handler"):
            return args.workflow_handler(args) or 0
        if args.action == "init":
            initialize(args)
        elif args.action in {"index", "pack", "show", "headings", "links", "verify"}:
            engine_operation(args)
        elif args.action == "execute":
            return run_case(args)
        elif args.action == "openapi":
            inventory(args)
        elif args.action == "record":
            record(args)
        else:
            run, _, _ = load(args.run)
            render(run)
            print(run / "log.md")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
