"""Archiva y compara corridas de Copilot sobre un encargo común de QA V6."""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
V6 = HERE.parent
sys.path.insert(0, str(V6 / "src"))

from audit import inspect, publication_code  # noqa: E402
from benchmark_report import compare  # noqa: E402
from contracts import BROWSER_FLOWS, observed_time, required_text, string_list  # noqa: E402
from management_report import render_html  # noqa: E402
from markdown import inline, table, write_markdown  # noqa: E402
from publication import write_delivery  # noqa: E402
from session import ROOT, WORK, append, load, read_json, run_id, write_json  # noqa: E402
from token_meter import STAGES, model_id, token_report, usage_config  # noqa: E402

RESULTS = ROOT / "evaluate-llm" / "resultados"
PHASES = ("analisis", "diseno", "ejecucion")
PLAYWRIGHT_RESULTS = {"passed", "failed", "partial"}
TRACKING = "evaluate-llm.json"


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def load_run(value):
    path = Path(value).expanduser()
    return load(WORK / run_id(value) if path.name == value else path)


def harness_fingerprint():
    paths = [
        *V6.glob("*.md"),
        *V6.glob("requirements-*.txt"),
        *(V6 / "src").rglob("*.py"),
        *(V6 / "templates").glob("*.*"),
        *HERE.glob("*.py"),
        HERE / "comparacion.html",
        HERE / "PROMPT.md",
    ]
    return fingerprint(
        json.dumps(
            [
                (str(path.relative_to(V6)), fingerprint(path.read_bytes()))
                for path in sorted(paths)
            ]
        ).encode()
    )


def validate_benchmark(data):
    for key in ("id", "title", "version", "environment", "setup"):
        required_text(data, key)
    run_id(data["id"])
    revision = data["corpus_revision"]
    if revision is not None and (
        not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{64}", revision)
    ):
        raise ValueError(
            "corpus_revision debe contener la revisión SHA-256 del índice o null."
        )
    flows = string_list(data, "browser_flows", allow_empty=True)
    if set(flows) - BROWSER_FLOWS.keys() or len(set(flows)) != len(flows):
        raise ValueError("browser_flows admite web_ui y swagger_ui, una vez cada uno.")
    rubric = data["rubric"]
    if not isinstance(rubric, dict) or set(rubric) != set(PHASES):
        raise ValueError("La rúbrica debe incluir analisis, diseno y ejecucion.")
    ids = []
    for phase in PHASES:
        checks = rubric[phase]
        if not isinstance(checks, list) or not checks:
            raise ValueError(f"Faltan comprobaciones para {phase}.")
        for item in checks:
            ids.append(run_id(required_text(item, "id")))
            required_text(item, "expected")
    if len(set(ids)) != len(ids):
        raise ValueError("Los IDs de la rúbrica deben ser únicos.")


def freeze(args):
    data = read_json(args.config)
    validate_benchmark(data)
    task = Path(args.consigna).read_bytes()
    if not task.decode("utf-8").strip():
        raise ValueError("La consigna común está vacía.")
    target = RESULTS / data["id"]
    if target.exists() or target.is_symlink():
        raise ValueError(
            "El benchmark ya existe. Usá otro ID para cambiar las condiciones."
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=target.parent) as temporary:
        output = Path(temporary) / target.name
        output.mkdir()
        (output / "consigna.md").write_bytes(task)
        write_json(
            output / "benchmark.json",
            {
                **data,
                "consigna_sha256": fingerprint(task),
                "harness_sha256": harness_fingerprint(),
            },
        )
        output.rename(target)
    print(target)


def benchmark(identifier):
    folder = RESULTS / run_id(identifier)
    path = folder / "benchmark.json"
    data = read_json(path)
    if (
        data["id"] != identifier
        or fingerprint((folder / "consigna.md").read_bytes()) != data["consigna_sha256"]
    ):
        raise ValueError("La consigna congelada cambió. Creá otro benchmark.")
    return folder, data, fingerprint(path.read_bytes())


def check_build(meta, data):
    if any(meta[key] != data[key] for key in ("version", "environment")):
        raise ValueError("La versión o el entorno de la corrida difiere del benchmark.")


def assigned(run):
    assignment = read_json(run / TRACKING)
    folder, data, digest = benchmark(assignment["benchmark"])
    if (
        assignment["benchmark_sha256"] != digest
        or data["harness_sha256"] != harness_fingerprint()
    ):
        raise ValueError(
            "Cambió el benchmark o el harness. Conservá las versiones congeladas."
        )
    return folder, data, assignment


def prepare(args):
    run, meta, events = load_run(args.run)
    if any(
        event["kind"] in {"case", "execution"} or "token_stage" in event
        for event in events
    ):
        raise ValueError("Vinculá una sesión nueva antes de analizar o diseñar casos.")
    folder, data, digest = benchmark(args.benchmark)
    check_build(meta, data)
    if data["harness_sha256"] != harness_fingerprint():
        raise ValueError("El harness cambió desde que se congeló el benchmark.")
    expected = model_id(args.modelo_esperado)
    if not expected:
        raise ValueError("Indicá el ID exacto del modelo informado por el proveedor.")
    tracking = {
        "benchmark": data["id"],
        "benchmark_sha256": digest,
        "label": run_id(args.modelo),
        "expected_model": expected,
    }
    if (run / TRACKING).is_file():
        current = read_json(run / TRACKING)
        if any(current.get(key) != value for key, value in tracking.items()):
            raise ValueError("La sesión ya está vinculada a otro modelo o benchmark.")
    else:
        write_json(run / TRACKING, tracking)
    meter = token_report(run, meta, events)
    # La comprobación inicial usa las mismas llamadas de referencia que tokens-check.
    if (
        not meter
        or "entries" not in meter
        or (meter["blocked"] and not meter.get("baseline_only"))
    ):
        raise ValueError("Primero verificá la fuente nativa con tokens-check.")
    observed = {entry[6] for entry in meter["entries"]}
    if observed != {expected}:
        raise ValueError(
            "La telemetría inicial no confirma el modelo esperado en todas las llamadas."
        )
    write_json(run / TRACKING, {**tracking, "initial_model_verified": True})
    print(folder / "consigna.md")


def finish(args):
    run, _, events = load_run(args.run)
    assigned(run)
    if not any(event.get("benchmark_finished") for event in events):
        append(
            run,
            {
                "kind": "note",
                "phase": "evaluacion-llm",
                "observation": "Fin del trabajo de QA para el benchmark.",
                "benchmark_finished": True,
            },
        )
    print(run)


def stage_metrics(events, calls, finished):
    cuts = [
        (event["token_stage"], event["time_utc"])
        for event in events
        if "token_stage" in event
    ]
    ordered = [(key, stamp) for key, stamp in cuts if key != "preparacion"]
    complete = [key for key, _ in ordered] == [*PHASES, "cierre"] and (
        not finished or observed_time(finished) >= observed_time(ordered[-1][1])
    )
    durations = {}
    if complete:
        for (key, start), (_, end) in zip(ordered, ordered[1:]):
            durations[key] = round(
                (observed_time(end) - observed_time(start)).total_seconds(), 3
            )
        if finished:
            durations["cierre"] = round(
                (
                    observed_time(finished) - observed_time(ordered[-1][1])
                ).total_seconds(),
                3,
            )
    use = {}
    for key, label in STAGES.items():
        rows = [
            entry for entry in calls if entry[1] == label and None not in entry[4:6]
        ]
        use[key] = {
            "calls": len(rows),
            "input": sum(entry[4] for entry in rows) if rows else None,
            "output": sum(entry[5] for entry in rows) if rows else None,
            "seconds": durations.get(key),
        }
    return use, complete


def check_stage_work(events, plan, check_brain):
    cuts = {
        event["token_stage"]: observed_time(event["time_utc"])
        for event in events
        if "token_stage" in event
    }
    live = [event for event in events if event["kind"] == "execution"]
    designed = (
        plan and cuts["diseno"] <= observed_time(plan["frozen_at"]) <= cuts["ejecucion"]
    )
    executed = all(
        cuts["ejecucion"] <= observed_time(event.get("started_at") or event["time_utc"])
        and observed_time(event.get("finished_at") or event["time_utc"])
        <= cuts["cierre"]
        for event in live
    )
    recovered = any(
        event.get("phase") == "pack"
        and event.get("exit_code") == 0
        and event.get("passages")
        and cuts["analisis"] <= observed_time(event["time_utc"]) <= cuts["diseno"]
        for event in events
    )
    return designed and executed and (not check_brain or recovered)


def summarize(events, report, data, assignment, run, name, finished):
    meter = report["tokens"] or {}
    calls = meter.get("entries", [])
    measured = [entry for entry in calls if None not in entry[4:6]]
    stage, marks_ok = stage_metrics(events, calls, finished)
    observed = Counter()
    token_models = Counter()
    for entry in calls:
        observed[entry[6]] += 1
        if None not in entry[4:6]:
            token_models[entry[6]] += sum(entry[4:6])
    packs = [
        event
        for event in events
        if event["kind"] == "note"
        and event.get("phase") == "pack"
        and event.get("exit_code") == 0
    ]
    indexed = {
        event["result"]["revision"]
        for event in events
        if event.get("phase") == "index"
        and event.get("exit_code") == 0
        and event.get("result", {}).get("revision")
    }
    revisions = indexed | {
        event["revision"] for event in packs if event.get("revision")
    }
    attempts = [event for rows in report["attempts"].values() for _, event in rows]
    plan = report["plan"] or {}
    reasons = []
    if (
        not finished
        or not meter.get("latest")
        or observed_time(meter["latest"]) < observed_time(finished)
    ):
        reasons.append("La telemetría todavía no alcanza el cierre registrado.")
    if meter.get("blocked", True):
        reasons.append(meter.get("reason") or "Falta una fuente de tokens válida.")
    if not assignment.get("initial_model_verified") or set(observed) != {
        assignment["expected_model"]
    }:
        reasons.append("Identidad del modelo incompleta, distinta o mezclada.")
    if not marks_ok:
        reasons.append("Faltan cortes de etapa ordenados y únicos.")
    elif not check_stage_work(events, plan, bool(data["corpus_revision"])):
        reasons.append(
            "El plan, la recuperación documental o los intentos quedaron fuera de su etapa."
        )
    if (
        not plan
        or not PLAYWRIGHT_RESULTS.intersection(report["latest"].values())
        or publication_code(report) != 0
    ):
        reasons.append("La ejecución V6 quedó incompleta o con problemas de evidencia.")
    if set(plan.get("browser_flows", [])) != set(data["browser_flows"]):
        reasons.append("Los recorridos Playwright del plan difieren del benchmark.")
    if data["browser_flows"] and not any(
        event.get("browser_ready") is True for event in events
    ):
        reasons.append("No se observó un preflight exitoso de Playwright.")
    if revisions != ({data["corpus_revision"]} if data["corpus_revision"] else set()):
        reasons.append(
            "La revisión observada del segundo cerebro difiere del benchmark."
        )
    if data["corpus_revision"] and (
        data["corpus_revision"] not in indexed
        or not any(pack.get("passages") for pack in packs)
    ):
        reasons.append(
            "Faltan la indexación y la recuperación documental de la corrida."
        )
    config = usage_config(run)
    return {
        "schema": "qa-llm/1",
        **assignment,
        "run": name,
        "conversation_sha256": fingerprint(config["scope"].encode())
        if config
        else None,
        "cutoff_utc": meter.get("latest"),
        "telemetry_source": meter.get("source"),
        "finished_utc": finished,
        "issues": reasons,
        "models": [
            {"id": key, "calls": count, "tokens": token_models.get(key)}
            for key, count in sorted(observed.items(), key=lambda item: item[0] or "")
        ],
        "total_input": sum(entry[4] for entry in measured) if measured else None,
        "total_output": sum(entry[5] for entry in measured) if measured else None,
        "stages": stage,
        "brain": {
            "revisions": sorted(revisions),
            "packs": len(packs),
            "source_appearances": sum(event.get("sources") or 0 for event in packs),
            "passages": sum(event.get("passages") or 0 for event in packs),
        },
        "planned_cases": [case["id"] for case in plan.get("cases", [])],
        "cases": [
            {
                "id": key,
                "requirement": case["requirement"],
                "result": report["latest"][key],
                "attempts": len(report["attempts"][key]),
                "evidence": sorted(
                    {
                        item["evidence"]
                        for number, event in report["attempts"][key]
                        if number not in report["invalid_attempts"]
                        and event["status"] in PLAYWRIGHT_RESULTS
                        for item in (event, *event["results"])
                        if item.get("evidence") in report["evidence"]
                    }
                ),
            }
            for key, case in report["cases"].items()
        ],
        "attempts": len(attempts),
        "playwright_attempts": sum(
            event["execution_method"] == "playwright" for event in attempts
        ),
        "retries": len(attempts)
        - sum(bool(rows) for rows in report["attempts"].values()),
    }


def archive(args):
    run, meta, events = load_run(args.run)
    folder, data, assignment = assigned(run)
    check_build(meta, data)
    name = run_id(run.name)
    destination = folder / "modelos" / assignment["label"] / name
    if destination.exists() or destination.is_symlink():
        raise ValueError(
            "La corrida ya está archivada. Usá otro ID para otra sesión de Copilot."
        )
    report = inspect(run, meta, events)
    finished = next(
        (event["time_utc"] for event in events if event.get("benchmark_finished")), None
    )
    summary = summarize(events, report, data, assignment, run, name, finished)
    if summary["issues"] and not args.incompleta:
        raise ValueError(
            " ".join(summary["issues"])
            + " Usá --incompleta si la corrida terminó bloqueada."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temporary:
        output = Path(temporary) / name
        write_delivery(run, meta, events, report, output)
        (output / "reporte gerencial.html").write_text(
            render_html(run, meta, events, report), encoding="utf-8"
        )
        write_json(output / "medicion.json", summary)
        write_markdown(
            output / "resumen llm.md",
            [
                f"# {inline(assignment['label'])} · {inline(name)}",
                "",
                f"- Modelo esperado · {inline(assignment['expected_model'])}",
                f"- Corte UTC de la fuente · {inline(summary['cutoff_utc'])}",
                f"- Casos iniciales · {len(summary['planned_cases'])}",
                f"- Casos registrados · {len(summary['cases'])}",
                f"- Intentos · {summary['attempts']} · Playwright · {summary['playwright_attempts']}",
                f"- Reintentos · {summary['retries']}",
                f"- Consultas documentales recuperadas en paquetes · {summary['brain']['packs']}",
                f"- Pasajes recuperados · {summary['brain']['passages']}",
                "",
                *table(
                    ("Modelo observado", "Llamadas", "Tokens con contador"),
                    (
                        (inline(row["id"]), row["calls"], inline(row["tokens"]))
                        for row in summary["models"]
                    ),
                ),
                *[f"- {inline(reason)}" for reason in summary["issues"]],
                "",
                "[Informe QA](informe%20final.md) · [Casos](casos.md) · [Ejecuciones](ejecuciones.md) · [Consumo por etapa](metricas.md)",
            ],
        )
        output.rename(destination)
    print(destination)


def review(args):
    folder, data, digest = benchmark(args.benchmark)
    target = folder / "modelos" / run_id(args.modelo) / run_id(args.id)
    summary = read_json(target / "medicion.json")
    if summary["benchmark_sha256"] != digest:
        raise ValueError("La corrida corresponde a otra versión de la rúbrica.")
    review_data = read_json(args.archivo)
    reviewer = required_text(review_data, "reviewer")
    decisions = review_data["checks"]
    if not isinstance(decisions, dict):
        raise ValueError(
            "checks debe ser un objeto con una decisión por ID de la rúbrica."
        )
    expected = {item["id"] for checks in data["rubric"].values() for item in checks}
    if set(decisions) != expected:
        raise ValueError("Completá exactamente todos los IDs de la rúbrica.")
    cases = {item["id"]: item for item in summary["cases"]}
    lines = [f"# Revisión independiente · {inline(reviewer)}", ""]
    for phase in PHASES:
        lines += [f"## {STAGES[phase]}", ""]
        for item in data["rubric"][phase]:
            identifier = item["id"]
            row = decisions[identifier]
            if type(row.get("met")) is not bool:
                raise ValueError(f"{identifier} requiere met true o false.")
            reason = required_text(row, "reason")
            refs = string_list(row, "evidence")
            ids = string_list(row, "cases", allow_empty=True)
            for ref in refs:
                path = target / ref
                if (
                    Path(ref).is_absolute()
                    or not path.resolve().is_relative_to(target.resolve())
                    or path.suffix != ".md"
                    or not path.is_file()
                ):
                    raise ValueError(f"Referencia Markdown inválida en {identifier}.")
            if set(ids) - cases.keys():
                raise ValueError(f"Caso inexistente en {identifier}.")
            if row["met"] and phase in ("diseno", "ejecucion") and not ids:
                raise ValueError(f"Vinculá los casos que cumplen {identifier}.")
            if (
                row["met"]
                and phase == "ejecucion"
                and any(
                    not set(cases[key]["evidence"]).intersection(refs) for key in ids
                )
            ):
                raise ValueError(
                    f"Cada caso validado en {identifier} requiere evidencia del intento."
                )
            links = " · ".join(f"[{inline(ref)}]({quote(ref)})" for ref in refs)
            lines += [
                f"- **{inline(identifier)}** · {'Cumplido' if row['met'] else 'No cumplido'} · {inline(reason)}",
                f"  - {links}",
                *([f"  - Casos · {inline(', '.join(ids))}"] if ids else []),
            ]
        lines.append("")
    if (target / "revision.json").exists():
        raise ValueError("Esta corrida ya tiene una revisión registrada.")
    write_markdown(target / "revision.md", lines)
    write_json(target / "revision.json", {"reviewer": reviewer, "checks": decisions})
    print(target / "revision.md")


def report(args):
    folder, data, digest = benchmark(args.benchmark)
    compare(folder, data, digest, PHASES, STAGES)
    print(folder / "comparacion.html")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True)
    for name, description, handler, options in (
        (
            "congelar",
            "Fijar la consigna y la rúbrica comunes",
            freeze,
            ("config", "consigna"),
        ),
        (
            "preparar",
            "Vincular la sesión y verificar el modelo",
            prepare,
            ("benchmark", "run", "modelo", "modelo-esperado"),
        ),
        ("finalizar", "Marcar el cierre de la sesión de QA", finish, ("run",)),
        ("archivar", "Guardar las evidencias por modelo y corrida", archive, ("run",)),
        (
            "revisar",
            "Registrar la revisión independiente",
            review,
            ("benchmark", "modelo", "id", "archivo"),
        ),
        (
            "comparar",
            "Generar los gráficos y el informe Markdown",
            report,
            ("benchmark",),
        ),
    ):
        command = commands.add_parser(name, help=description)
        for option in options:
            command.add_argument(f"--{option}", required=True)
        if handler is archive:
            command.add_argument("--incompleta", action="store_true")
        command.set_defaults(handler=handler)
    args = parser.parse_args()
    try:
        args.handler(args)
    except (OSError, ValueError, KeyError, AttributeError, TypeError) as error:
        parser.exit(2, f"Evaluación LLM · {error}\n")


if __name__ == "__main__":
    main()
