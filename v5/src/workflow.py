"""Herramientas de preparación y ejecución repetible para una sesión."""

import importlib.util
import os
from http.client import HTTPException
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from markdown import inline, table, write_markdown
from runners import Unavailable, http_request, run_case
from session import append, load, read_json, timestamp, write_json


def preflight(args):
    run, meta, _ = load(args.run)
    profile = meta["profile"]
    probes = []
    for operation in profile.get("http_operations", []):
        expectations = operation.get("probe")
        if expectations is None:
            continue
        try:
            _, observed = http_request(
                profile, operation, {}, None, expectations.get("actor", "anonymous")
            )
        except Unavailable as error:
            observed = {"state": "unavailable", "reason": str(error)}
        except (OSError, HTTPException):
            observed = {
                "state": "unavailable",
                "reason": "La conexión o lectura no se completó.",
            }
        else:
            ready = observed["http_status"] == expectations.get("status", 200) and (
                "content_type" not in expectations
                or observed["content_type"] == expectations["content_type"]
            )
            observed["state"] = "ready" if ready else "unexpected_response"
        probes.append(
            {
                "path": operation["path"].split("?", 1)[0],
                "expected": expectations.get("status", 200),
                **observed,
            }
        )

    playwright_installed = importlib.util.find_spec("playwright") is not None
    reference = f"evidencias/preflight-{uuid4().hex}.md"
    write_markdown(
        run / reference,
        [
            "# Disponibilidad inicial",
            "",
            f"- Hora UTC · {timestamp()}",
            f"- Paquete Playwright · {'Presente' if playwright_installed else 'Ausente'}",
            *[
                f"- Credencial para {inline(actor)} · {'Presente' if os.environ.get(env) else 'Ausente'}"
                for actor, env in profile.get("credentials", {}).items()
            ],
            "",
            *table(
                ("Sonda", "HTTP esperado", "HTTP observado", "Resultado", "Detalle"),
                (
                    (
                        inline(probe["path"]),
                        probe["expected"],
                        inline(probe.get("http_status")),
                        probe["state"],
                        inline(probe.get("reason") or probe.get("content_type")),
                    )
                    for probe in probes
                ),
            ),
        ],
    )
    ready_count = sum(probe["state"] == "ready" for probe in probes)
    append(
        run,
        {
            "kind": "note",
            "phase": "preflight",
            "observation": f"Sondas HTTP listas: {ready_count} de {len(probes)}.",
            "evidence": reference,
        },
    )
    print(run / reference)
    return 3 if any(probe["state"] != "ready" for probe in probes) else 0


def freeze_plan(args):
    run, _, events = load(args.run)
    cases = [event for event in events if event["kind"] == "case"]
    if not cases:
        raise ValueError("Registrá los casos antes de congelar el plan.")
    target = run / "plan.json"
    if target.exists():
        raise ValueError("El plan ya está congelado.")
    catalog = None
    if args.requirements:
        catalog = read_json(args.requirements)
        if (
            not isinstance(catalog, list)
            or not catalog
            or not all(isinstance(item, str) and item.strip() for item in catalog)
            or len(set(catalog)) != len(catalog)
        ):
            raise ValueError("El catálogo debe ser una lista de IDs únicos no vacíos.")
    write_json(target, {"frozen_at": timestamp(), "catalog": catalog, "cases": cases})
    append(
        run,
        {
            "kind": "note",
            "phase": "plan",
            "observation": f"Plan congelado con {len(cases)} casos.",
        },
    )
    print(target)


def suite(args):
    run, _, events = load(args.run)
    manifest = Path(args.manifest).resolve()
    items = read_json(manifest)
    if not isinstance(items, list) or not items:
        raise ValueError("El manifiesto debe ser una lista de casos.")
    known_cases = {event["id"] for event in events if event["kind"] == "case"}
    if not all(
        isinstance(item, dict)
        and isinstance(item.get("case"), str)
        and item["case"] in known_cases
        and item.get("via") in ("http", "playwright")
        and ("body" not in item or isinstance(item["body"], str))
        and (
            "seed" not in item
            or item["via"] == "playwright"
            and type(item["seed"]) is int
        )
        for item in items
    ):
        raise ValueError(
            "Cada entrada necesita un caso registrado y un canal http o playwright."
        )
    results = []
    for item in items:
        body = manifest.parent / item["body"] if "body" in item else None
        try:
            code = run_case(
                SimpleNamespace(
                    run=run,
                    case=item["case"],
                    via=item["via"],
                    body=body,
                    seed=item.get("seed"),
                )
            )
        except (ValueError, OSError) as error:
            print(f"{item['case']}: {error}")
            code = 2
        results.append({"case": item["case"], "via": item["via"], "exit_code": code})
    summary = ", ".join(f"{row['case']}={row['exit_code']}" for row in results)
    append(
        run,
        {
            "kind": "note",
            "phase": "suite",
            "observation": f"Códigos del runner por caso: {summary}.",
        },
    )
    codes = {result["exit_code"] for result in results}
    return next((code for code in (2, 1, 3) if code in codes), 0)
