"""Catálogo versionado, ejecución por release y resultados para CI."""

import hashlib
import json
import shlex
import sys
from dataclasses import dataclass
from time import sleep
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from xml.etree import ElementTree as ET

from audit import inspect
from contracts import validate_case
from json_tools import valid_path
from bindings import TOKEN
from markdown import inline, write_markdown
from openapi_contract import operation_for, read_spec, response_schema
from records import store_records
from runners import checks_for, profile_for_run, run_case
from session import RESULTS, WORK, load, read_json, run_id, write_json
from workflow import freeze_plan


@dataclass
class LoadedSuite:
    profile: dict
    corpus: Path | None
    cases: list
    manifest: list
    bodies: dict
    uploads: dict
    requirements: list | None
    provenance: dict
    contracts: dict


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()


def case_digest(case):
    return digest({k: v for k, v in case.items() if k not in ("time_utc", "azure")})


def inside(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError("Falta una ruta de archivo.")
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Archivo ausente o fuera del directorio declarado: {name}")
    return path


def verify_sources(case, corpus):
    revisions = {}
    for source in case["sources"]:
        if corpus is None:
            raise ValueError(
                f"{case['id']}: indicá --corpus para resolver las fuentes."
            )
        path = inside(corpus, source["path"])
        content = path.read_bytes()
        text = content.decode("utf-8-sig")
        if "start" in source and not (
            1 <= source["start"] <= source["end"] <= len(text.splitlines())
        ):
            raise ValueError(f"{case['id']}: rango fuera de {source['path']}.")
        if (
            source.get("locator")
            and source["locator"].casefold() not in text.casefold()
        ):
            raise ValueError(f"{case['id']}: localizador ausente en {source['path']}.")
        sha = hashlib.sha256(content).hexdigest()
        if source.get("sha256") and sha != source["sha256"]:
            raise ValueError(f"{case['id']}: cambió la fuente {source['path']}.")
        revisions[source["path"]] = sha
    return revisions


def load_suite(args):
    suite_file = Path(args.suite).resolve()
    root = suite_file.parent
    config = read_json(suite_file)
    if config.get("schema") != "agentic-qc/suite-1":
        raise ValueError("Versión de suite desconocida.")
    run_id(config["app"])
    profile_file = (
        Path(args.profile).resolve()
        if args.profile
        else inside(root, config["profile"])
    )
    profile = profile_for_run(
        read_json(profile_file), chrome_visible=args.chrome_visible
    )
    corpus = (
        Path(args.corpus).resolve()
        if args.corpus
        else (root / config["corpus"]).resolve()
        if config.get("corpus")
        else None
    )
    cases = read_json(inside(root, config["cases"]))
    manifest_path = inside(root, config["manifest"])
    manifest = read_json(manifest_path)
    if (
        not isinstance(cases, list)
        or not cases
        or not isinstance(manifest, list)
        or not manifest
    ):
        raise ValueError("La suite requiere casos y un manifiesto no vacíos.")
    catalog = {}
    for case in cases:
        if not isinstance(case, dict) or case.get("kind") != "case":
            raise ValueError("El catálogo debe contener registros kind=case.")
        validate_case(case)
        key = run_id(case["id"])
        if key in catalog:
            raise ValueError(f"ID de caso duplicado: {key}")
        catalog[key] = case
    inputs = {}
    seen = set()
    sources = {}
    definitions = {}
    fixtures = {}
    uploads = {}
    contracts = {}
    spec_file = inside(root, config["openapi"]) if config.get("openapi") else None
    spec = read_spec(spec_file) if spec_file else None
    producers = {"RUN_ID": None}
    for item in manifest:
        key, channel = item["case"], item["via"]
        if (
            key not in catalog
            or key in seen
            or channel not in ("api", "http", "playwright", "db")
        ):
            raise ValueError(f"Entrada desconocida o duplicada en el manifiesto: {key}")
        dependencies = item.get("depends_on", [])
        if not isinstance(dependencies, list) or any(
            dep not in seen for dep in dependencies
        ):
            raise ValueError(f"{key}: declará dependencias previas en el manifiesto.")
        case = catalog[key]
        if not isinstance(item.get("capture", {}), dict):
            raise ValueError("capture debe asociar nombres con rutas JSON.")
        if "body" in item and (
            channel not in ("api", "http") or case["http"]["method"] in ("GET", "HEAD")
        ):
            raise ValueError(f"{key}: cuerpo incompatible con el canal o método.")
        if case.get("browser_flow") and channel != "playwright":
            raise ValueError(f"{key}: el recorrido requiere navegador.")
        if channel in ("api", "http"):
            op = case["http"]
            if not any(
                item["method"] == op["method"]
                and item["path"] == op["path"]
                and op.get("actor", "anonymous") in item.get("actors", ["anonymous"])
                for item in profile.get("http_operations", [])
            ):
                raise ValueError(
                    f"{key}: la operación o el actor quedan fuera del perfil."
                )
        if channel == "playwright" and case.get("browser_path") not in profile.get(
            "browser_paths", []
        ):
            raise ValueError(f"{key}: ruta de navegador fuera del perfil.")
        if channel == "db":
            from database_runner import query_arguments

            query_arguments(profile, case)
        poll = item.get("poll", {})
        if poll and (
            not isinstance(poll, dict)
            or set(poll) != {"attempts", "interval_seconds"}
            or type(poll["attempts"]) is not int
            or not 1 <= poll["attempts"] <= 10
            or type(poll["interval_seconds"]) is not int
            or not 1 <= poll["interval_seconds"] <= 30
            or not (
                channel == "db"
                or channel in ("http", "api")
                and case["http"]["method"] in ("GET", "HEAD")
            )
        ):
            raise ValueError(
                f"{key}: poll requiere lectura, hasta 10 intentos y un intervalo de 1 a 30 segundos."
            )
        definitions[key] = case_digest(case)
        sources.update(verify_sources(case, corpus))
        if case["oracle_status"] == "pending":
            raise ValueError(f"{key}: resolvé el esperado antes de promover el caso.")
        if spec and channel in ("api", "http"):
            operation_for(spec, case)
            contracts[key] = str(spec_file)
        for criterion in case["criteria"]:
            check = criterion.get("check", {})
            if check.get("type") == "response_schema":
                if not spec_file:
                    raise ValueError(f"{key}: falta OpenAPI para validar la respuesta.")
                check["schema"] = response_schema(spec_file, case, check)
        checks_for(case, "http" if channel == "api" else channel)
        hashes = {}
        if "body" in item:
            body = inside(manifest_path.parent, item["body"]).read_bytes()
            json.loads(body)
            fixtures[key] = body
            hashes["body"] = hashlib.sha256(body).hexdigest()
        for step in case.get("browser_steps", []):
            if step["type"] == "upload":
                name = step["value"]
                fixture_root = (root / "fixtures").resolve()
                fixture_file = inside(fixture_root, name)
                data = fixture_file.read_bytes()
                uploads[fixture_file.relative_to(fixture_root).as_posix()] = data
                hashes[name] = hashlib.sha256(data).hexdigest()
        used = set(TOKEN.findall(json.dumps(case))) | set(
            TOKEN.findall(fixtures.get(key, b"").decode())
        )
        if used - producers.keys() or any(
            producers[n] and producers[n] not in dependencies for n in used
        ):
            raise ValueError(
                f"{key}: el valor dinámico requiere un productor previo en depends_on."
            )
        for name, path in item.get("capture", {}).items():
            if (
                channel != "api"
                or not name.isidentifier()
                or name in producers
                or not valid_path(path)
            ):
                raise ValueError(f"{key}: captura de ID inválida.")
            producers[name] = key
        inputs[key] = digest(
            {"case": case_digest(case), "step": item, "fixtures": hashes}
        )
        seen.add(key)
    selected = [catalog[item["case"]] for item in manifest]
    requirements = (
        read_json(inside(root, config["requirements"]))
        if "requirements" in config
        else None
    )
    if requirements is not None and (
        not isinstance(requirements, list)
        or not requirements
        or not all(isinstance(r, str) and r.strip() for r in requirements)
        or len(set(requirements)) != len(requirements)
    ):
        raise ValueError("Catálogo de requisitos inválido.")
    dependencies = {}
    for package in ("playwright", "PyYAML", "jsonschema", "psycopg"):
        try:
            dependencies[package] = version(package)
        except PackageNotFoundError:
            continue
    provenance = {
        "app": config["app"],
        "framework": "9.0.0",
        "suite": digest([list(inputs.items()), requirements, sources]),
        "cases": definitions,
        "inputs": inputs,
        "sources": sources,
        "profile": digest(profile),
        "runtime": sys.version.split()[0],
        "dependencies": dependencies,
        "contract": digest(spec) if spec else None,
    }
    return LoadedSuite(
        profile, corpus, selected, manifest, fixtures, uploads, requirements, provenance,
        contracts,
    )


def verdict(run, meta, events):
    report = inspect(run, meta, events)
    plan = report["plan"] or {}
    required = [c["id"] for c in plan.get("cases", [])]
    rows = []
    for key in required:
        attempts = report["attempts"].get(key, [])
        last = attempts[-1][1] if attempts else {}
        rows.append(
            {
                "case": key,
                "first": report["first"][key],
                "status": report["latest"][key],
                "attempts": len(attempts),
                "duration_ms": sum(e.get("duration_ms") or 0 for _, e in attempts),
                "evidence": last.get("evidence"),
                "observation": last.get("observation", meta.get("bloqueos_preflight", {}).get(key, "Sin intento.")),
            }
        )
    states = {r["status"] for r in rows}
    missing = sorted(
        set(plan.get("catalog") or [])
        - {c["requirement"] for c in plan.get("cases", [])}
    )
    decision = "aprobada"
    if "failed" in states:
        decision = "rechazada"
    elif not rows or states != {"passed"} or report["issues"] or missing:
        decision = "inconclusa"
    tokens = report["tokens"] or {}
    totals = tokens.get("totals", {})
    measurements = {
        "duration_ms_attempts": sum(r["duration_ms"] for r in rows),
        "token_input": sum(r[1] for r in totals.values()) if totals else None,
        "token_output": sum(r[2] for r in totals.values()) if totals else None,
        "token_partial": tokens.get("blocked") if tokens else None,
    }
    return {
        "schema": "agentic-qc/result-1",
        "measurements": measurements,
        "build": meta["version"],
        "environment": meta["environment"],
        "decision": decision,
        "missing_requirements": missing,
        "issues": report["issues"],
        "provenance": meta.get("provenance", {}),
        "cases": rows,
    }


def write_ci(output, result):
    rows = result["cases"]
    xml = ET.Element(
        "testsuite",
        name=result["provenance"].get("app", "AgenticQC"),
        tests=str(len(rows)),
        failures=str(sum(r["status"] == "failed" for r in rows)),
        skipped=str(sum(r["status"] not in ("passed", "failed") for r in rows)),
    )
    for row in rows:
        test = ET.SubElement(
            xml,
            "testcase",
            classname=xml.get("name"),
            name=row["case"],
            time=str(row["duration_ms"] / 1000),
        )
        if row["status"] != "passed":
            element = "failure" if row["status"] == "failed" else "skipped"
            ET.SubElement(test, element, message=row["status"]).text = row[
                "observation"
            ]
    ET.ElementTree(xml).write(
        output / "junit.xml", encoding="utf-8", xml_declaration=True
    )
    write_json(output / "resultado.json", result)


def decision_code(result):
    return {"aprobada": 0, "rechazada": 1, "inconclusa": 3}[result["decision"]]


def gate(args):
    run, meta, events = load(args.run)
    result = verdict(run, meta, events)
    write_ci(run, result)
    print(f"{result['decision']} · {run / 'resultado.json'}")
    return decision_code(result)


def blocked(run, case, reason):
    _, meta, events = load(run)
    ref = f"evidencias/{case['id']}-{uuid4().hex}.md"
    write_markdown(run / ref, [f"# {case['id']}", "", reason])
    store_records(
        run,
        meta,
        events,
        {
            "kind": "execution",
            "case_id": case["id"],
            "execution_method": "suite",
            "executor": "runner",
            "status": "blocked",
            "classification": "inconclusive",
            "observation": reason,
            "evidence": ref,
            "results": [
                {
                    "id": c["id"],
                    "status": "blocked",
                    "observation": reason,
                    "evidence": ref,
                }
                for c in case["criteria"]
            ],
        },
    )


def replay(args):
    from qa import initialize
    from management_report import export_html
    from publication import publish
    from regressions import load_application

    if args.suite and (args.regressions or args.new_suite):
        raise ValueError("--regressions y --new-suite requieren --app.")
    if args.suite:
        suite, batch_by_case = load_suite(args), {}
    else:
        suite, batch_by_case = load_application(args)
    provenance = suite.provenance
    app = provenance["app"]
    if args.action == "validate":
        print(f"{app} · {len(suite.cases)} casos · {provenance['suite']}")
        return
    ruta_bloqueos = getattr(args, "bloqueos_preflight", None)
    bloqueos = read_json(ruta_bloqueos) if ruta_bloqueos else {}
    if (
        not isinstance(bloqueos, dict)
        or bloqueos.keys() - {case["id"] for case in suite.cases}
        or not all(isinstance(reason, str) and reason for reason in bloqueos.values())
    ):
        raise ValueError("El informe de preflight contiene casos o motivos inválidos.")
    identifier = run_id(
        args.id
        or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:8]
    )
    run = WORK / identifier
    if run.is_symlink() or WORK.is_symlink() or (RESULTS / identifier).exists():
        raise ValueError("Usá una carpeta local y un ID nuevo.")
    params = SimpleNamespace(
        run=run,
        title=app,
        environment=args.env,
        version=args.build,
        profile=None,
        corpus=suite.corpus,
        benchmark=False,
        requirements=None,
        browser_flow=None,
        name=None,
        zip=True,
    )
    initialize(params)
    _, meta, events = load(run)
    cmd = [
        "qc",
        "run",
        "--env",
        args.env,
        "--build",
        args.build,
    ]
    for flag in ("suite", "app", "regressions", "new_suite", "profile", "corpus"):
        if getattr(args, flag):
            cmd += ["--" + flag.replace("_", "-"), str(getattr(args, flag))]
    if args.chrome_visible:
        cmd.append("--chrome-visible")
    if getattr(args, "build_ref", None):
        provenance = {**provenance, "build_ref": args.build_ref}
        cmd.extend(["--build-ref", args.build_ref])
    meta.update(
        profile=suite.profile,
        provenance=provenance,
        replay=shlex.join(cmd),
        contracts=suite.contracts,
        bloqueos_preflight=bloqueos,
    )
    write_json(run / "run.json", meta)
    for name, data in suite.uploads.items():
        path = run / "fixtures" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for key, data in suite.bodies.items():
        (run / "artifacts" / f"{key}.json").write_bytes(data)
    manifest_snapshot = [
        {**item, "body": f"artifacts/{item['case']}.json"}
        if item["case"] in suite.bodies
        else item
        for item in suite.manifest
    ]
    write_json(run / "suite.json", manifest_snapshot)
    store_records(run, meta, events, suite.cases)
    if suite.requirements:
        params.requirements = run / "artifacts" / "requisitos.json"
        write_json(params.requirements, suite.requirements)
    freeze_plan(params)
    completed = {}
    bindings = {}
    for case, item in zip(suite.cases, suite.manifest):
        key = case["id"]
        if key in bloqueos:
            completed[key] = 3
            continue
        failed_dependencies = [
            dep for dep in item.get("depends_on", []) if completed[dep] != 0
        ]
        if failed_dependencies:
            blocked(
                run,
                case,
                "Requisito previo pendiente · " + ", ".join(failed_dependencies),
            )
            completed[key] = 3
            continue
        try:
            execution = SimpleNamespace(
                run=run,
                case=key,
                via=item["via"],
                seed=item.get("seed"),
                bindings=bindings.setdefault(batch_by_case.get(key), {"RUN_ID": identifier}),
                capture=item.get("capture"),
                body=run / "artifacts" / f"{key}.json" if key in suite.bodies else None,
            )
            poll = item.get("poll", {})
            for attempt in range(poll.get("attempts", 1)):
                if attempt:
                    sleep(poll["interval_seconds"])
                completed[key] = run_case(execution)
                if completed[key] != 1:
                    break
        except (ValueError, OSError) as error:
            blocked(run, case, str(error))
            completed[key] = 3
    _, meta, events = load(run)
    result = verdict(run, meta, events)
    write_ci(run, result)
    write_markdown(
        run / "evaluacion.md",
        [
            f"## Recomendación de salida · {result['decision']}",
            "",
            "Cada caso de la suite es obligatorio.",
            "",
            f"Repetir la suite con `{meta['replay']}`.",
        ],
    )
    write_markdown(
        run / "analisis.md",
        [
            "# Fuentes del catálogo aprobado",
            "",
            *[
                f"- {inline(path)} · {sha}"
                for path, sha in provenance["sources"].items()
            ],
        ],
    )
    write_markdown(
        run / "metricas.md",
        [
            "# Medición de ejecución",
            "",
            "Corrida de regresión sin intervención del agente.",
        ],
    )
    publish(params)
    export_html(params)
    print(f"{result['decision']} · {RESULTS / identifier / 'resultado.json'}")
    return decision_code(result)
