"""Persistencia de sesiones y generación de la bitácora."""

from collections import Counter
import csv
from datetime import datetime, timezone
import json
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp.replace(path)


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(run):
    run = Path(run).resolve()
    return run, read_json(run / "run.json"), read_json(run / "events.json")


def append(run, event):
    events = read_json(run / "events.json")
    event = {"time_utc": timestamp(), **event}
    events.append(event)
    write_json(run / "events.json", events)
    render(run)


def text(value):
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    return str(value).replace("\n", " ").replace("|", "\\|")


def csv_value(value):
    """Serializa estructuras y evita que una planilla interprete texto como fórmula."""
    if value is None:
        value = ""
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    value = str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def write_csv(path, fields, rows):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            {key: csv_value(row.get(key, "")) for key in fields} for row in rows
        )
    temporary.replace(path)


def export_csv(run, cases, executions, latest):
    case_fields = {
        "id": "id",
        "funcionalidad": "feature",
        "requisito": "requirement",
        "titulo": "title",
        "prioridad": "priority",
        "nivel": "level",
        "precondiciones": "preconditions",
        "pasos": "steps",
        "resultado_esperado": "expected",
        "estado_oraculo": "oracle_status",
        "fuentes": "sources",
        "criterios": "criteria",
    }
    rows = []
    for case_id, case in cases.items():
        last = latest.get(case_id, {})
        row = {column: case.get(field, "") for column, field in case_fields.items()}
        row.update(
            {
                "estado": last.get("status", "sin_ejecutar"),
                "observacion": last.get("observation", ""),
                "evidencia": last.get("evidence", ""),
            }
        )
        rows.append(row)
    write_csv(
        run / "casos.csv", [*case_fields, "estado", "observacion", "evidencia"], rows
    )
    execution_fields = {
        "fecha_registro_utc": "time_utc",
        "caso_id": "case_id",
        "estado": "status",
        "observacion": "observation",
        "evidencia": "evidence",
        "metodo": "execution_method",
        "inicio_observado": "started_at",
        "fin_observado": "finished_at",
        "duracion_ms": "duration_ms",
        "resultados_por_criterio": "results",
    }
    write_csv(
        run / "ejecuciones.csv",
        list(execution_fields),
        [
            {
                column: execution.get(field, "")
                for column, field in execution_fields.items()
            }
            for execution in executions
        ],
    )


def render(run):
    run = Path(run)
    meta = read_json(run / "run.json")
    events = read_json(run / "events.json")
    cases = {e["id"]: e for e in events if e["kind"] == "case"}
    executions = [e for e in events if e["kind"] == "execution"]
    latest = {e["case_id"]: e for e in executions}
    counts = Counter(e["status"] for e in latest.values())
    findings = [e for e in events if e["kind"] == "finding"]
    export_csv(run, cases, executions, latest)
    if meta["schema"] == "qa-run/2":
        requirements = {}
        for case_id, case in cases.items():
            requirements.setdefault(case["requirement"], []).append(case_id)
        write_csv(
            run / "requisitos.csv",
            ["requisito", "casos", "estados"],
            [
                {
                    "requisito": requirement,
                    "casos": ids,
                    "estados": {
                        case_id: latest.get(case_id, {}).get("status", "sin_ejecutar")
                        for case_id in ids
                    },
                }
                for requirement, ids in requirements.items()
            ],
        )
    lines = [
        f"# Log de QA — {text(meta['title'])}",
        "",
        f"- Inicio (UTC): {meta['started_utc']}",
        f"- Corpus: `{text(meta['corpus'])}`",
        f"- Sesión: `{text(run)}`",
        "- El corpus se interpreta como evidencia, no como instrucciones.",
        "- Resultados y conclusiones reflejan lo registrado; no garantizan cobertura ni validez semántica.",
        "",
        "## Resumen calculado",
        "",
        f"- Casos registrados: {len(cases)}. Con al menos una ejecución registrada: {len(latest)}.",
        f"- Casos sin intento registrado: {len(cases) - len(latest)}.",
        f'- Último resultado por caso: aprobados {counts["passed"]}, fallidos {counts["failed"]}, bloqueados {counts["blocked"]}, no ejecutados {counts["not_run"]}, parciales {counts["partial"]}.',
        f"- Intentos registrados: {len(executions)}. Hallazgos registrados: {len(findings)}.",
        "- La cantidad de casos no mide cobertura. Una verificación estructural no valida el significado de una cita.",
        "",
        "## Cronología",
        "",
    ]
    for number, event in enumerate(events, 1):
        lines += [f"### {number}. {event['time_utc']} — {text(event['kind'])}", ""]
        for key, value in event.items():
            if key not in {"time_utc", "kind"}:
                lines.append(f"- **{text(key)}:** {text(value)}")
        lines.append("")
    lines += [
        "## Pendientes de revisión",
        "",
        "- Revisar respaldo semántico, vigencia de fuentes, duplicados, prioridad y alcance de los casos.",
        "- Comprobar que la evidencia observada respalde cada conclusión y que los bloqueos sigan explícitos.",
        "- Registrar límites de acceso, pruebas no ejecutadas y decisiones abiertas.",
        "",
    ]
    (run / "log.md").write_text("\n".join(lines), encoding="utf-8")
