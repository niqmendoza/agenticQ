"""Publica las notas revisables de una corrida para Obsidian."""

import shutil
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from audit import STATES, inspect, publication_code
from contracts import BROWSER_FLOWS
from markdown import inline, source_label, table, write_markdown
from session import RESULTS, TEMPLATES, load, run_id
from token_meter import token_lines, write_token_evidence


def evidence_link(reference, notes):
    if reference in notes:
        return f"[{Path(reference).stem}]({reference})"
    return "No disponible" if reference else "—"


def case_details(case):
    sources = [source_label(source) for source in case["sources"]]
    browser_flow = BROWSER_FLOWS.get(case.get("browser_flow"))
    criteria = [
        f"- {inline(item['id'])} · {inline(item['expected'])}"
        for item in case["criteria"]
    ]
    clarification = case.get("oracle_rationale") or case.get("oracle_pending_reason")
    expected = case.get("step_expected", [""] * len(case["steps"]))
    steps = [
        f"{number}. {inline(action)}"
        + (f" · Esperado · {inline(result)}" if result else "")
        for number, (action, result) in enumerate(zip(case["steps"], expected), 1)
    ]
    return [
        f"### {inline(case['id'])} · {inline(case['title'])}",
        "",
        f"- Funcionalidad y requisito · {inline(case['feature'])} / {inline(case['requirement'])}",
        f"- Prioridad y nivel · {inline(case['priority'])} / {inline(case['level'])}",
        f"- Escenario · {inline(case['scenario'])}",
        *([f"- Recorrido Playwright · {browser_flow}"] if browser_flow else []),
        *([f"- Motivo · {inline(case['rationale'])}"] if case.get("rationale") else []),
        f"- Resultado esperado · {inline(case['expected'])}",
        f"- Oráculo · {inline(case['oracle_status'])}"
        + (f" · {inline(clarification)}" if clarification else ""),
        *[f"- Fuente · {inline(source)}" for source in sources],
        *[f"- Precondición · {inline(value)}" for value in case["preconditions"]],
        "",
        "**Pasos**",
        "",
        *steps,
        "",
        "**Criterios**",
        "",
        *criteria,
        "",
    ]


def render_plan(report):
    plan = report["plan"]
    if plan is None:
        return ["# Plan de casos", "", "No hay un plan congelado."]
    return [
        "# Plan de casos",
        "",
        f"Congelado en {inline(plan['frozen_at'])}. Casos iniciales · {len(plan['cases'])}.",
        "",
        *[line for case in plan["cases"] for line in case_details(case)],
    ]


def render_cases(report):
    initial = {case["id"] for case in (report["plan"] or {}).get("cases", [])}
    return [
        "# Casos",
        "",
        *table(
            ("ID", "Caso", "Plan", "Primer intento", "Último estado", "Intentos"),
            (
                (
                    inline(key),
                    inline(case["title"]),
                    "Sin congelar"
                    if report["plan"] is None
                    else "Inicial"
                    if key in initial
                    else "Agregado",
                    report["first"][key],
                    report["latest"][key],
                    len(report["attempts"][key]),
                )
                for key, case in report["cases"].items()
            ),
        ),
        *[line for case in report["cases"].values() for line in case_details(case)],
    ]


def render_attempts(events, report):
    lines = [
        "# Ejecuciones",
        "",
        "Cada entrada conserva un intento. Las horas incluyen su zona.",
        "",
    ]
    counts = Counter()
    for number, event in enumerate(events, 1):
        if event["kind"] != "execution":
            continue
        case_id = event["case_id"]
        audit_status = (
            " · evidencia inválida" if number in report["invalid_attempts"] else ""
        )
        counts[case_id] += 1
        lines += [
            f"## {inline(case_id)} · intento {counts[case_id]} · evento {number}",
            "",
            f"- Estado registrado · {inline(event['status'])}{audit_status}",
            f"- Método y ejecutor · {inline(event['execution_method'])} / {inline(event['executor'])}",
            f"- Escenario · {inline(report['cases'][case_id]['scenario'])}",
            f"- Clasificación · {inline(event.get('classification'))}",
            f"- Inicio / fin observado · {inline(event.get('started_at'))} / {inline(event.get('finished_at'))}",
            f"- Duración en ms · {inline(event.get('duration_ms'))}",
            f"- Observación · {inline(event['observation'])}",
            f"- Evidencia del intento · {evidence_link(event.get('evidence'), report['evidence'])}",
            "",
            *table(
                ("Criterio", "Estado", "Observación", "Evidencia"),
                (
                    (
                        inline(result["id"]),
                        inline(result["status"]),
                        inline(result["observation"]),
                        evidence_link(result.get("evidence"), report["evidence"]),
                    )
                    for result in event["results"]
                ),
            ),
        ]
    if not counts:
        lines.append("No hay intentos registrados.")
    return lines


def render_log(meta, events, report):
    lines = [
        "# Log",
        "",
        f"- Inicio UTC · {inline(meta['started_utc'])}",
        "",
        "## Cronología",
        "",
    ]
    for number, event in enumerate(events, 1):
        kind = event["kind"]
        label = event.get("id") or event.get("case_id") or event.get("phase")
        observation = event.get("observation") or event.get("title")
        reference = event.get("evidence")
        link = f" · {evidence_link(reference, report['evidence'])}" if reference else ""
        lines.append(
            f"- {number} · {inline(event['time_utc'])} · {kind} · {inline(label)} · {inline(observation)}{link}"
        )
    return lines


def final_report(meta, report):
    lines = [
        f"# Informe final · {inline(meta['title'])}",
        "",
        f"- Entorno · {inline(meta['environment'])}",
        f"- Versión o build · {inline(meta['version'])}",
        f"- Inicio UTC · {inline(meta['started_utc'])}",
        f"- Casos registrados · {len(report['cases'])}",
        f"- Intentos registrados · {sum(map(len, report['attempts'].values()))}",
        "",
        *table(
            ("Estado", "Primer intento por caso", "Último estado por caso"),
            (
                (state, report["first_counts"][state], report["latest_counts"][state])
                for state in STATES
            ),
        ),
        "## Hallazgos",
        "",
    ]
    if not report["findings"]:
        lines += ["Sin hallazgos registrados.", ""]
    for item in report["findings"]:
        cases = ", ".join(item["case_ids"])
        lines += [
            f"### {inline(item['id'])} · {inline(item['classification'])} / {inline(item['confidence'])}",
            "",
            f"- Casos · {inline(cases)}",
            f"- Observación · {inline(item['observation'])}",
            f"- Interpretación · {inline(item['interpretation'])}",
            f"- Severidad · {inline(item.get('severity'))}",
            f"- Pendiente · {inline(item['pending'])}",
            f"- Evidencia · {evidence_link(item.get('evidence'), report['evidence'])}",
            "",
        ]
    if report["tokens"] and report["tokens"]["blocked"]:
        lines += [
            f"**Medición de tokens pendiente · {inline(report['tokens']['reason'])}**",
            "",
        ]
    if report["browser_blocked"]:
        lines += ["**Playwright bloqueado. Ver preflight y log.**", ""]
    if report["missing_browser_flows"]:
        missing = ", ".join(
            BROWSER_FLOWS[key] for key in report["missing_browser_flows"]
        )
        lines += [f"**Verificación Playwright pendiente · {missing}.**", ""]
    lines += ["## Trazabilidad de requisitos", ""]
    catalog = report["catalog"]
    groups = report["groups"]
    if catalog is None:
        lines += [
            "Sin catálogo independiente. La cobertura total queda indeterminada.",
            "",
        ]
    else:
        missing = sorted(set(catalog) - groups.keys())
        outside = sorted(groups.keys() - set(catalog))
        lines += [
            f"- Requisitos del catálogo · {len(catalog)}",
            f"- Requisitos sin caso · {inline(', '.join(missing))}",
            f"- Requisitos de casos fuera del catálogo · {inline(', '.join(outside))}",
            "",
        ]
    lines += table(
        ("Requisito", "Casos y último estado", "Evidencia de todos los casos"),
        (
            (
                inline(requirement),
                inline(", ".join(f"{key} ({report['latest'][key]})" for key in ids))
                or "—",
                "Criterios documentados aprobados"
                if ids
                and all(
                    report["latest"][key] == "passed"
                    and report["cases"][key]["oracle_status"] == "documented"
                    for key in ids
                )
                else "Pendiente o parcial",
            )
            for requirement, ids in sorted(groups.items())
        ),
    )
    lines += ["## Integridad de la entrega", ""]
    lines += [f"- {inline(issue)}" for issue in report["issues"]] or [
        "La auditoría estructural no detectó referencias de evidencia inválidas. Revisá el respaldo semántico."
    ]
    lines += [
        "",
        (
            "[Plan inicial](plan%20casos.md) · [Casos](casos.md) · [Ejecuciones](ejecuciones.md) · "
            "[Log](log.md) · [Análisis documental](analisis%20segundo%20cerebro.md) · [Métricas](metricas.md)"
        ),
        "",
    ]
    return lines


def metric_summary(report):
    attempts = [event for rows in report["attempts"].values() for _, event in rows]
    durations = [
        event["duration_ms"]
        for event in attempts
        if event.get("duration_ms") is not None
    ]
    executors = Counter(event["executor"] for event in attempts)
    return [
        "## Indicadores calculados del registro",
        "",
        f"- Intentos con duración medida · {len(durations)} de {len(attempts)}",
        f"- Suma de duraciones en ms · {sum(durations) if durations else 'No disponible'}",
        f"- Casos con reintento · {sum(len(rows) > 1 for rows in report['attempts'].values())}",
        f"- Intentos por ejecutor · runner {executors['runner']}, agente {executors['agent']}, humano {executors['human']}",
        "",
        "La suma de duraciones cubre los intentos medidos. El tiempo total de la corrida se registra por separado.",
        "",
    ]


def publish(args):
    run, meta, events = load(args.run)
    report = inspect(run, meta, events)
    target = RESULTS / run_id(args.name or run.name)
    if RESULTS.is_symlink():
        raise ValueError("resultados debe ser una carpeta local a V5.")
    if target.exists() or target.is_symlink():
        raise ValueError("La entrega ya existe. Usá --name para publicar una revisión.")
    archive = target.with_suffix(".zip")
    if args.zip and (archive.exists() or archive.is_symlink()):
        raise ValueError("El ZIP ya existe. Usá --name para publicar una revisión.")
    RESULTS.mkdir(exist_ok=True)

    def input_lines(name):
        source = run / name
        if not source.is_file():
            source = TEMPLATES / name
        return source.read_text(encoding="utf-8").splitlines()

    with TemporaryDirectory(dir=run) as temporary:
        output = Path(temporary) / target.name
        output.mkdir()
        tokens = report["tokens"]
        token_summary = token_lines(tokens)
        if tokens and "entries" in tokens:
            reference = "evidencias/consumo-tokens-v5.md"
            if reference in report["evidence"]:
                raise ValueError(
                    "La referencia consumo-tokens-v5.md está reservada para V5."
                )
            (output / "evidencias").mkdir()
            write_token_evidence(output / reference, tokens)
            token_summary += [f"[Detalle por llamada]({reference})", ""]
        for name, lines in {
            "plan casos.md": render_plan(report),
            "casos.md": render_cases(report),
            "ejecuciones.md": render_attempts(events, report),
            "log.md": render_log(meta, events, report),
            "analisis segundo cerebro.md": input_lines("analisis.md"),
            "metricas.md": [
                "# Métricas de la corrida",
                "",
                *token_summary,
                *input_lines("metricas.md"),
                "",
                *metric_summary(report),
            ],
            "informe final.md": [
                *final_report(meta, report),
                *input_lines("evaluacion.md"),
            ],
        }.items():
            write_markdown(output / name, lines)
        for relative, source in report["evidence"].items():
            destination = output / relative
            destination.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, destination)
        if args.zip:
            bundle = shutil.make_archive(
                str(Path(temporary) / "evidencias"),
                "zip",
                root_dir=temporary,
                base_dir=output.name,
            )
        output.rename(target)
        if args.zip:
            Path(bundle).rename(archive)
    print(archive if args.zip else target)
    return publication_code(report)
