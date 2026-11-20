"""Genera el reporte gerencial autocontenido desde la auditoría de la corrida."""

from datetime import datetime
from html import escape
from pathlib import Path
from string import Template
from tempfile import TemporaryDirectory

from audit import STATES, inspect, publication_code
from contracts import BROWSER_FLOWS
from markdown import source_label
from session import ROOT, TEMPLATES, load, run_id

REPORTS = ROOT / "reportes"
STATUS = {
    "passed": "Aprobado",
    "failed": "Fallido",
    "blocked": "Bloqueado",
    "partial": "Parcial",
    "not_run": "No ejecutado",
    "unattempted": "Sin intento",
    "invalid_evidence": "Evidencia inválida",
}
CLASSIFICATION = {
    "product": "Producto",
    "environment": "Entorno",
    "runner": "Herramienta de prueba",
    "inconclusive": "Sin diagnóstico",
}


def text(value):
    return escape(str(value), quote=True)


def listing(items, css_class=""):
    if not items:
        return ""
    return (
        f'<ul class="{css_class}">'
        + "".join(f"<li>{text(item)}</li>" for item in items)
        + "</ul>"
    )


def render_counts(report, regressions):
    counts = [("Casos registrados", len(report["cases"]))]
    if regressions is not None:
        counts.extend(
            [
                ("Casos del catálogo", len(regressions["saved"])),
                ("Casos nuevos", len(regressions["new"])),
            ]
        )
    if report["plan"] is not None:
        planned = report["planned_count"]
        observed = planned - len(report["planned_unobserved"])
        counts.append(
            ("Casos del plan con ejecución observada", f"{observed} de {planned}")
        )
    counts.extend(
        (STATUS[state], report["latest_counts"][state])
        for state in STATES
        if report["latest_counts"][state]
    )
    retries = sum(len(attempts) > 1 for attempts in report["attempts"].values())
    if retries:
        counts.append(("Casos con reintentos", retries))
    return "".join(
        f"<div><dt>{text(label)}</dt><dd>{count}</dd></div>" for label, count in counts
    )


def attempts_details(case, report):
    attempts = report["attempts"][case["id"]]
    if not attempts:
        return ""
    criteria = {item["id"]: item["expected"] for item in case["criteria"]}
    details = []
    for index, (event_number, event) in enumerate(attempts, 1):
        state = (
            "invalid_evidence"
            if event_number in report["invalid_attempts"]
            else event["status"]
        )
        details.append(
            f"Intento {index} · {event['execution_method']} · {STATUS[state]} · {event['observation']}"
        )
        details.extend(
            f"{criteria[result['id']]} · {STATUS[result['status']]} · {result['observation']}"
            for result in event["results"]
        )
    return f"<details><summary>Intentos y criterios ({len(attempts)})</summary>{listing(details)}</details>"


def render_cases(report):
    cases = []
    for case_id, case in report["cases"].items():
        state = report["latest"][case_id]
        reason = (
            case.get("rationale")
            or f"Verificar el requisito {case['requirement']} de {case['feature']}."
        )
        attempts = report["attempts"][case_id]
        if state == "invalid_evidence":
            observation = "El último intento tiene evidencia pendiente de validar."
        elif attempts:
            observation = attempts[-1][1]["observation"]
        else:
            observation = "No se registró un intento para este caso."
        label = f"{case_id} · {case['feature']}"
        browser_flow = BROWSER_FLOWS.get(case.get("browser_flow"))
        if browser_flow:
            label += f" · {browser_flow}"
        steps = "".join(f"<li>{text(step)}</li>" for step in case["steps"])
        sources = listing([source_label(source) for source in case["sources"]])
        source_details = f"<p>Fuentes documentales</p>{sources}" if sources else ""
        cases.append(
            f'<article class="record case" id="case-{text(case_id)}">'
            f'<div><span class="label">{text(label)}</span>'
            f"<h3>{text(case['title'])}</h3></div>"
            f'<div><span class="label">Por qué se incluyó</span><p>{text(reason)}</p></div>'
            f'<div><span class="label">Último resultado</span>'
            f'<p class="status {state}">{STATUS[state]}</p><p>{text(observation)}</p></div>'
            f"<details><summary>Escenario y pasos</summary><p>{text(case['scenario'])}</p>"
            f"<ol>{steps}</ol>"
            f"<p>Resultado esperado · {text(case['expected'])}</p>"
            f"<p>Requisito · {text(case['requirement'])}</p>"
            f"{source_details}</details>"
            f"{attempts_details(case, report)}</article>"
        )
    return (
        '<div class="records">' + "".join(cases) + "</div>"
        if cases
        else "<p>No hay casos registrados.</p>"
    )


def render_findings(report):
    findings = []
    for finding in report["findings"]:
        if finding["id"] in report["invalid_findings"]:
            confidence = "Evidencia pendiente de validar"
        elif finding["confidence"] == "confirmed":
            confidence = (
                "Arreglo verificado"
                if finding.get("fix_status") == "verified_fixed"
                else "Confirmado"
            )
        else:
            confidence = "Hipótesis"
        title = f"{finding['id']} · {CLASSIFICATION[finding['classification']]} · {confidence}"
        case_links = ", ".join(
            f'<a href="#case-{text(case_id)}">{text(case_id)}</a>'
            for case_id in finding["case_ids"]
        )
        severity = (
            f'<p class="muted">Severidad · {text(finding["severity"])}</p>'
            if finding.get("severity")
            else ""
        )
        linked = f'<p class="muted">Casos · {case_links}</p>' if case_links else ""
        findings.append(
            f'<article class="record"><h3>{text(title)}</h3>'
            f"<p>{text(finding['observation'])}</p>{severity}"
            f"<p>Pendiente · {text(finding['pending'])}</p>{linked}</article>"
        )
    return (
        '<div class="records">' + "".join(findings) + "</div>"
        if findings
        else "<p>Sin hallazgos registrados.</p>"
    )


def render_scope(report):
    notes = []
    if report["plan"] is None:
        notes.append("Plan de casos pendiente de congelar.")
    elif report["planned_unobserved"]:
        missing = ", ".join(report["planned_unobserved"])
        notes.append(f"Casos del plan sin ejecución observada · {missing}.")
    if report["tokens"] and report["tokens"]["blocked"]:
        notes.append(f"Medición de tokens pendiente · {report['tokens']['reason']}")
    if report["browser_blocked"]:
        notes.append("Playwright bloqueado. Ver preflight y log.")
    if report["missing_browser_flows"]:
        missing = ", ".join(
            BROWSER_FLOWS[key] for key in report["missing_browser_flows"]
        )
        notes.append(f"Verificación Playwright pendiente · {missing}.")
    if report["catalog"] is None:
        notes.append(
            "La cobertura total queda indeterminada sin un catálogo de requisitos."
        )
    else:
        missing = sorted(set(report["catalog"]) - report["groups"].keys())
        notes.append(
            f"Requisitos sin caso registrado · {', '.join(missing)}"
            if missing
            else "Todos los requisitos del catálogo tienen al menos un caso registrado."
        )
    pending = [
        key
        for key, state in report["latest"].items()
        if state in ("blocked", "partial", "not_run", "unattempted", "invalid_evidence")
    ]
    if pending:
        notes.append(f"Casos con verificación pendiente · {', '.join(pending)}")
    if report["issues"]:
        notes.append(
            "La auditoría encontró incidencias de evidencia. Consultá el informe técnico."
        )
    return listing(notes, "notes")


def render_html(run, meta, events, report):
    from release import verdict

    decision = verdict(run, meta, events)["decision"]
    summary = report["summary"]
    summary = f"Recomendación para la release · {decision}." + (
        f" {summary}" if summary else ""
    )
    template = Template(
        (TEMPLATES / "reporte-gerencial.html").read_text(encoding="utf-8")
    )
    return template.substitute(
        title=text(meta["title"]),
        run=text(run.name),
        environment=text(meta["environment"]),
        version=text(meta["version"]),
        started=datetime.fromisoformat(meta["started_utc"]).strftime(
            "%d/%m/%Y %H:%M UTC"
        ),
        summary=f"<p>{text(summary)}</p>" if summary else "",
        counts=render_counts(report, meta.get("provenance", {}).get("regressions")),
        cases=render_cases(report),
        findings=render_findings(report),
        scope=render_scope(report),
    )


def export_html(args):
    run, meta, events = load(args.run)
    report = inspect(run, meta, events)
    name = run_id(args.name or run.name)
    target = REPORTS / f"{name}.html"
    if REPORTS.is_symlink():
        raise ValueError("reportes debe ser una carpeta local a V6.")
    if target.exists() or target.is_symlink():
        raise ValueError("El HTML ya existe. Usá --name para exportar una revisión.")
    html = render_html(run, meta, events, report)
    REPORTS.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=REPORTS) as temporary:
        draft = Path(temporary) / target.name
        draft.write_text(html, encoding="utf-8")
        draft.rename(target)
    print(target)
    return publication_code(report)
