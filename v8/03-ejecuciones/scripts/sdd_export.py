"""Prepara una propuesta SDD por defecto de producto confirmado y abierto."""

from pathlib import Path
from string import Template
from tempfile import TemporaryDirectory

from audit import inspect
from markdown import inline, source_label
from session import ROOT, TEMPLATES, load, run_id

FIXES = ROOT / "SDD fixes"


def bullets(items):
    return "\n".join(f"- {inline(item)}" for item in items)


def render_fix(template, item, report, meta, run_name):
    cases = [report["cases"][case_id] for case_id in item["case_ids"]]
    guidance = item.get("sdd", {})
    title = guidance.get("title") or f"Arreglo propuesto · {item['id']}"
    cases_label = ", ".join(f"{case['id']} ({case['requirement']})" for case in cases)

    if guidance.get("reproduction"):
        reproduction = "\n".join(
            f"{number}. {inline(step)}"
            for number, step in enumerate(guidance["reproduction"], 1)
        )
    else:
        reproduction = "\n\n".join(
            f"**{inline(case['id'])} · {inline(case['scenario'])}**\n\n"
            + (
                bullets([f"Precondición · {step}" for step in case["preconditions"]])
                + "\n\n"
                if case["preconditions"]
                else ""
            )
            + "\n".join(
                f"{number}. {inline(step)}"
                for number, step in enumerate(case["steps"], 1)
            )
            for case in cases
        )
    if meta.get("replay"):
        reproduction += (
            "\n\nComando sobre el checkout del piloto\n\n```sh\n"
            + meta["replay"]
            + "\n```"
        )
        reproduction += "\n\nRevisión de suite · " + meta["provenance"]["suite"]
    expected = guidance.get("expected")
    expected_section = (
        inline(expected)
        if expected
        else bullets(f"{case['id']} · {case['expected']}" for case in cases)
    )

    sources = dict.fromkeys(
        f"Contrato del caso · {source_label(source)}"
        for case in cases
        for source in case["sources"]
    )
    sources.update(
        dict.fromkeys(
            f"Referencia para revisar · {source_label(source)}"
            for source in guidance.get("sources", [])
        )
    )
    evidence = f"[Evidencia de la corrida]({item['evidence']})"
    for case in cases:
        for _, attempt in report["attempts"][case["id"]]:
            for row in attempt["results"]:
                if row["status"] == "failed":
                    evidence += f"\n- {inline(case['id'])} · {inline(row['id'])} · {inline(row['observation'])}"
    if guidance.get("evidence_summary"):
        evidence += f"\n\n{inline(guidance['evidence_summary'])}"
    suggestion = (
        f"Componente a revisar · {inline(guidance['component'])}.\n\n{inline(guidance['suggestion'])}"
        if guidance
        else "La ubicación y el cambio propuesto quedan para revisión con las fuentes y el código vigente."
    )
    acceptance = guidance.get("acceptance") or [
        f"{case['id']} · {criterion['expected']}"
        for case in cases
        for criterion in case["criteria"]
    ]
    regression = guidance.get("regression") or [
        f"Reejecutar {case['id']} en el escenario original y registrar el resultado por criterio."
        for case in cases
    ]
    return template.substitute(
        title=inline(title),
        finding=inline(item["id"]),
        run=inline(run_name),
        environment=inline(meta["environment"]),
        version=inline(meta["version"]),
        cases=inline(cases_label) if cases_label else "Sin casos asociados.",
        severity=inline(item.get("severity"))
        if item.get("severity")
        else "Sin severidad registrada.",
        guidance_status="Propuesta para revisión"
        if guidance
        else "Borrador pendiente de completar",
        observation=inline(item["observation"]),
        impact=inline(guidance["impact"])
        if guidance.get("impact")
        else "Impacto sin registrar.",
        expected=expected_section or "Comportamiento esperado pendiente de confirmar.",
        reproduction=reproduction or "Pasos de reproducción pendientes de registrar.",
        evidence=evidence,
        sources=bullets(sources) or "Fuentes para revisar pendientes de identificar.",
        suggestion=suggestion,
        acceptance=bullets(acceptance) or "Criterios pendientes de confirmar.",
        regression=bullets(regression) or "Pruebas pendientes de definir.",
        pending=inline(item["pending"]),
    )


def export_fixes(args):
    run, meta, events = load(args.run)
    report = inspect(run, meta, events)
    eligible = [
        item
        for item in report["findings"]
        if item["classification"] == "product"
        and item["confidence"] == "confirmed"
        and item.get("fix_status", "open") == "open"
    ]
    invalid = [
        item["id"] for item in eligible if item["id"] in report["invalid_findings"]
    ]
    for item in invalid:
        print(f"{item} · Propuesta pendiente por evidencia inválida.")
    fixes = [item for item in eligible if item["id"] not in report["invalid_findings"]]
    if not fixes:
        print(
            "No hay defectos confirmados y abiertos con evidencia válida para entregar."
        )
        return 1 if invalid else 0

    target = FIXES / run_id(args.name or run.name)
    if FIXES.is_symlink():
        raise ValueError("SDD fixes debe ser una carpeta local a V6.")
    if target.exists() or target.is_symlink():
        raise ValueError(
            "La entrega SDD ya existe. Usá --name para exportar una revisión."
        )
    template = Template((TEMPLATES / "sdd-fix.md").read_text(encoding="utf-8"))
    FIXES.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=FIXES) as temporary:
        output = Path(temporary) / "entrega"
        output.mkdir()
        for item in fixes:
            import shutil

            dest = output / item["evidence"]
            dest.parent.mkdir(exist_ok=True)
            shutil.copyfile(report["evidence"][item["evidence"]], dest)
            identifier = run_id(item["id"])
            (output / f"{identifier}.md").write_text(
                render_fix(template, item, report, meta, run.name),
                encoding="utf-8",
            )
        output.rename(target)
    print(target)
    return 1 if invalid else 0
