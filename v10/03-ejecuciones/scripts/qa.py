#!/usr/bin/env python3
"""Operaciones reproducibles de una sesión de QA, sin ejecutar instrucciones del corpus."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from contextlib import nullcontext
from uuid import uuid4
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rutas import ANALISIS, cargar_motor

cargar_motor()

from azure_export import export_azure
from contracts import BROWSER_FLOWS
from json_tools import fixture_variant
from management_report import export_html
from mock_data import generate_mock_data
from publication import publish
from records import record
from runners import inventory, profile_for_run, run_case
from sdd_export import export_fixes
from session import (
    TEMPLATES,
    WORK,
    append,
    load,
    read_json,
    run_id,
    timestamp,
    write_json,
    writer,
)
from token_meter import SOURCES, STAGES, check_tokens, mark_stage
from workflow import freeze_plan, preflight, suite

ENGINE = ANALISIS / "brain.py"


def initialize(args):
    profile = profile_for_run(
        read_json(args.profile) if args.profile else {},
        chrome_visible=getattr(args, "chrome_visible", False),
    )
    corpus = Path(args.corpus).resolve() if args.corpus else None
    run = args.run.resolve()
    if corpus is not None and not corpus.is_dir():
        raise ValueError("El corpus debe ser un directorio existente.")
    if corpus is not None and (run == corpus or corpus in run.parents):
        raise ValueError("La sesión debe estar fuera del corpus.")
    run.mkdir(parents=True, exist_ok=False)
    (run / "artifacts").mkdir()
    (run / "evidencias").mkdir()
    for name in ("analisis.md", "metricas.md", "evaluacion.md"):
        shutil.copyfile(TEMPLATES / name, run / name)
    write_json(
        run / "run.json",
        {
            "schema": "qa-run/6",
            "tokens_required": args.benchmark,
            "profile": profile,
            "title": args.title,
            "environment": args.environment,
            "version": args.version,
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
            "observation": "Sesión creada.",
        },
    )
    print(run)


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
    started = timestamp()
    result = subprocess.run(
        command, check=False, capture_output=True, text=True, encoding="utf-8"
    )
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
    init.add_argument(
        "--benchmark", action="store_true", help="Exigir telemetría nativa"
    )
    init.add_argument("--corpus")
    init.add_argument("--profile", help="Perfil interno de HTTP, navegador o MCP")
    init.add_argument(
        "--chrome-visible", action="store_true", help="Usar el Chrome instalado con ventana"
    )
    init.add_argument("--title", required=True)
    init.add_argument("--environment", default="No informado")
    init.add_argument("--version", default="No verificada")
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
    event = sub.add_parser(
        "record", help="Registrar un caso, intento, hallazgo o nota JSON"
    )
    event.add_argument("--run", required=True)
    event.add_argument("--json", default="-", help="JSON desde un archivo o stdin")
    execute = sub.add_parser("execute", help="Ejecutar un caso funcional del perfil")
    execute.add_argument("--run", required=True)
    execute.add_argument("--case", required=True)
    execute.add_argument(
        "--via", choices=("http", "api", "playwright", "db"), required=True
    )
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
        if name == "preflight":
            command.add_argument(
                "--browser",
                action="store_true",
                help="Comprobar que Playwright puede abrir el navegador",
            )
        if name == "suite":
            command.add_argument("--manifest", required=True)
        if name == "freeze-plan":
            command.add_argument(
                "--browser-flow", action="append", choices=BROWSER_FLOWS
            )
            command.add_argument(
                "--requirements", help="Lista JSON de IDs del catálogo independiente"
            )
    tokens = sub.add_parser(
        "tokens-check", help="Comprobar una fuente de contadores nativos"
    )
    tokens.add_argument("--run", required=True)
    tokens.add_argument(
        "--file", required=True, help="Archivo JSONL de contadores autorizado"
    )
    tokens.add_argument("--format", choices=SOURCES, default="otel")
    tokens.add_argument(
        "--scope", help="Identificador de conversación si el archivo contiene varias"
    )
    tokens.set_defaults(workflow_handler=check_tokens)
    tokens_stage = sub.add_parser(
        "tokens-stage", help="Marcar un corte entre etapas de la corrida"
    )
    tokens_stage.add_argument("--run", required=True)
    tokens_stage.add_argument("--stage", required=True, choices=tuple(STAGES)[:-1])
    tokens_stage.set_defaults(workflow_handler=mark_stage)
    publication = sub.add_parser(
        "publish", help="Exportar la entrega Markdown a resultados/"
    )
    publication.add_argument("--run", required=True)
    publication.add_argument("--name", help="ID alternativo de publicación")
    publication.add_argument(
        "--zip", action="store_true", help="Empaquetar notas y evidencias de la corrida"
    )
    publication.set_defaults(workflow_handler=publish)
    for name, help_text, handler in (
        ("export-html", "Generar el reporte gerencial HTML", export_html),
        (
            "export-fixes",
            "Generar los Markdown SDD por defecto de producto",
            export_fixes,
        ),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--run", required=True)
        command.add_argument("--name", help="ID alternativo de exportación")
        command.set_defaults(workflow_handler=handler)
    azure = sub.add_parser(
        "export-azure", help="Generar el CSV de diseño de casos para Azure Test Plans"
    )
    azure.add_argument("--run", required=True)
    azure.add_argument(
        "--case", action="append", help="ID de caso a exportar. Se puede repetir."
    )
    azure.add_argument("--area", required=True, help="Ruta de área existente en Azure")
    azure.add_argument(
        "--assigned-to",
        default="",
        help="Identidad válida del proyecto si se asignan los casos",
    )
    azure.add_argument("--state", default="Design", help="Estado inicial de los casos")
    azure.add_argument("--name", help="ID alternativo de exportación")
    azure.set_defaults(workflow_handler=export_azure)
    mock = sub.add_parser("mock-data", help="Generar datos sintéticos reproducibles")
    mock.add_argument("--run", required=True)
    mock.add_argument(
        "--spec", required=True, help="Esquema JSON de los datos de prueba"
    )
    mock.add_argument("--name", required=True, help="Nombre del fixture generado")
    mock.add_argument("--seed", type=int, required=True)
    mock.add_argument("--count", type=int, default=1)
    mock.set_defaults(workflow_handler=generate_mock_data)
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
    from release_cli import register_commands

    register_commands(sub)
    args = parser.parse_args()
    try:
        if hasattr(args, "run"):
            candidate = WORK / run_id(args.run)
            if candidate.parent.is_symlink() or candidate.is_symlink():
                raise ValueError(
                    "La carpeta de trabajo de V6 debe ser local a este workspace."
                )
            args.run = candidate
        if args.action == "run" and not args.id:
            args.id = uuid4().hex
        target = (
            WORK / run_id(args.id)
            if args.action == "run"
            else getattr(args, "run", None)
        )
        with writer(target) if target else nullcontext():
            if hasattr(args, "workflow_handler"):
                return args.workflow_handler(args) or 0
            if args.action == "init":
                initialize(args)
            elif args.action in {"index", "pack", "show", "headings", "links"}:
                engine_operation(args)
            elif args.action == "execute":
                return run_case(args)
            elif args.action == "openapi":
                inventory(args)
            elif args.action == "record":
                record(args)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
