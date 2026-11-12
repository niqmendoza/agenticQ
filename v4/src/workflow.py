"""Herramientas de preparación y ejecución repetible para una sesión V4."""

import importlib.util
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
from urllib.error import URLError
from uuid import uuid4

from runners import Unavailable, http_request, run_case
from session import append, load, read_json, write_json


def preflight(args):
    run, meta, _ = load(args.run)
    profile = meta.get("profile")
    if profile is None:
        raise ValueError("preflight requiere una sesión con perfil.")
    probes = []
    for operation in profile.get("http_operations", []):
        if operation.get("probe") is not True:
            continue
        if operation["method"] != "GET":
            raise ValueError("Solo las operaciones GET pueden marcarse como probe.")
        try:
            _, observed = http_request(profile, operation, {}, None)
        except (Unavailable, URLError, OSError):
            observed = {"state": "unreachable"}
        else:
            observed["state"] = (
                "ready"
                if observed["http_status"] == 200
                and observed["content_type"] == "application/json"
                else "unexpected_response"
            )
        probes.append({"path": operation["path"], **observed})

    bearer_env = profile.get("bearer_env")
    result = {
        "probes": probes,
        "playwright_installed": importlib.util.find_spec("playwright") is not None,
        "bearer_present": bool(os.environ.get(bearer_env)) if bearer_env else None,
        "mcp_declared": profile.get("db_sources", []),
        "mcp_connection": "requires_host_check",
        "agent_token_telemetry": "requires_host_check",
    }
    path = run / "preflight.json"
    artifact = run / "artifacts" / f"preflight-{uuid4().hex}.json"
    write_json(artifact, result)
    write_json(path, result)
    append(
        run,
        {
            "kind": "note",
            "phase": "preflight",
            "observation": "Disponibilidad inicial registrada.",
            "artifact": artifact.relative_to(run).as_posix(),
        },
    )
    print(path)
    return 3 if any(probe["state"] != "ready" for probe in probes) else 0


def freeze_plan(args):
    run, _, events = load(args.run)
    if not any(event["kind"] == "case" for event in events):
        raise ValueError("Registrá los casos antes de congelar el plan.")
    if any(event["kind"] == "execution" for event in events):
        raise ValueError("Congelá el plan antes del primer intento.")
    target = run / "plan-casos.csv"
    with (run / "casos.csv").open("rb") as source, target.open("xb") as output:
        shutil.copyfileobj(source, output)
    append(
        run,
        {
            "kind": "note",
            "phase": "plan",
            "observation": "Plan congelado antes del primer intento.",
            "artifact": target.name,
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
            print(f'{item["case"]}: {error}')
            code = 2
        results.append({"case": item["case"], "via": item["via"], "exit_code": code})
    target = run / "suite.json"
    artifact = run / "artifacts" / f"suite-{uuid4().hex}.json"
    write_json(artifact, results)
    write_json(target, results)
    append(
        run,
        {
            "kind": "note",
            "phase": "suite",
            "observation": "Resultados del lote guardados.",
            "artifact": artifact.relative_to(run).as_posix(),
        },
    )
    print(target)
    codes = {result["exit_code"] for result in results}
    return next((code for code in (2, 1, 3) if code in codes), 0)
