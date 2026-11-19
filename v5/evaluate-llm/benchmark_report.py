"""Construye una comparación portable a partir de las corridas archivadas."""

from collections import Counter, defaultdict
from html import escape
from pathlib import Path
from statistics import median
from string import Template
from urllib.parse import quote

from markdown import inline, table, write_markdown
from session import read_json


def measured_total(start, end):
    return start + end if start is not None and end is not None else None


def sample(values):
    available = [value for value in values if value is not None]
    return f"{median(available):.1f} (n={len(available)})" if available else "—"


def read_runs(folder, digest):
    rows = []
    for path in sorted(folder.glob("modelos/*/*/medicion.json")):
        run = read_json(path)
        review_path = path.with_name("revision.json")
        review = read_json(review_path)["checks"] if review_path.is_file() else None
        issues = list(run["issues"])
        if run["benchmark_sha256"] != digest:
            issues.append("La corrida tiene otra versión del benchmark.")
        rows.append((path.parent, run, review, issues))
    counts = Counter(run["conversation_sha256"] for _, run, _, _ in rows)
    for _, run, _, issues in rows:
        scope = run["conversation_sha256"]
        if scope and counts[scope] > 1:
            issues.append("La misma conversación se usó en más de una corrida.")
    return rows


def metrics(runs, phases, rubric):
    groups = defaultdict(list)
    for _, run, review, issues in runs:
        if not issues:
            groups[run["label"], run["expected_model"]].append((run, review))

    for (label, model), rows in sorted(groups.items()):
        reviewed = sum(review is not None for _, review in rows)
        totals = [
            measured_total(run["total_input"], run["total_output"]) for run, _ in rows
        ]
        yield (
            label,
            model,
            "Total de la corrida",
            len(rows),
            reviewed,
            sample(totals),
            "—",
            "—",
            "—",
            "—",
            median(totals),
            None,
        )
        for phase, stage in phases.items():
            tokens = []
            times = []
            scores = []
            effective_cases = []
            efficiency = []
            checks = [item["id"] for item in rubric[phase]]
            for run, review in rows:
                stage_usage = run["stages"][phase]
                usage = measured_total(stage_usage["input"], stage_usage["output"])
                tokens.append(usage)
                times.append(stage_usage["seconds"])
                if review is None:
                    continue
                achieved = [review[check] for check in checks if review[check]["met"]]
                scores.append(100 * len(achieved) / len(checks))
                if phase != "analisis":
                    effective_cases.append(
                        len({case for row in achieved for case in row["cases"]})
                    )
                if achieved and usage is not None:
                    efficiency.append(usage / len(achieved))
            yield (
                label,
                model,
                stage,
                len(rows),
                reviewed,
                sample(tokens),
                sample(times),
                sample(scores),
                sample(effective_cases),
                sample(efficiency),
                None,
                median(scores) if scores else None,
            )


def bars(rows, suffix, *, maximum=None):
    if not rows:
        return "<p>Sin datos para este gráfico.</p>"
    maximum = maximum or max(value for _, value in rows) or 1
    return (
        "<ul class='chart'>"
        + "".join(
            f"<li><span>{escape(label)}</span><span class='track' aria-hidden='true'>"
            f"<span class='bar' style='width:{100 * value / maximum:.4f}%'></span></span>"
            f"<strong>{value:,.1f}{suffix}</strong></li>"
            for label, value in rows
        )
        + "</ul>"
    )


def html_table(columns, rows):
    headings = "".join(f"<th scope='col'>{escape(col)}</th>" for col in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f"<div class='scroll'><table><thead><tr>{headings}</tr></thead><tbody>{body}</tbody></table></div>"


def compare(folder, data, digest, phases, stages):
    runs = read_runs(folder, digest)
    labels = {key: stages[key] for key in phases}
    rows = list(metrics(runs, labels, data["rubric"]))
    columns = (
        "Modelo",
        "ID observado",
        "Etapa",
        "Corridas",
        "Revisadas",
        "Tokens",
        "Segundos",
        "Rúbrica (%)",
        "Casos validados",
        "Tokens por punto logrado",
    )
    notes = [
        "La tabla muestra medianas. n indica cuántas corridas aportaron datos a cada celda.",
        "La rúbrica mide puntos logrados sobre el total fijado por etapa. Los casos validados son casos distintos vinculados a puntos logrados en la revisión independiente.",
        "Tokens por punto logrado divide el consumo de la etapa por los puntos logrados en cada corrida con ambos datos. Una etapa sin puntos logrados o sin medición asignable queda sin cociente.",
        "El total incluye preparación, cierre y llamadas mixtas. Las llamadas que cruzan un corte se consignan como mixtas. Los segundos miden tiempo entre marcas e incluyen espera y herramientas.",
        "El consumo cubre lo que exportó el cliente del agente. Un resultado funcional fallido puede demostrar un punto de la rúbrica si se comprobó y quedó respaldado.",
    ]
    overview = [
        f"Build · {data['version']}   |   Entorno · {data['environment']}",
        f"Corridas archivadas · {len(runs)}   |   Comparables · {sum(not issues for _, _, _, issues in runs)}",
    ]
    outcomes = defaultdict(Counter)
    for _, run, review, issues in runs:
        counts = outcomes[run["label"], run["expected_model"]]
        counts["archived"] += 1
        counts["comparable"] += not issues
        counts["reviewed"] += not issues and review is not None
    outcome_columns = (
        "Modelo",
        "ID esperado",
        "Archivadas",
        "Comparables",
        "Revisadas",
    )
    outcome_rows = [
        (label, model, counts["archived"], counts["comparable"], counts["reviewed"])
        for (label, model), counts in sorted(outcomes.items())
    ]
    write_markdown(
        folder / "comparacion.md",
        [
            f"# {inline(data['title'])}",
            "",
            *[f"- {inline(line)}" for line in overview],
            "",
            "## Estado de las corridas por modelo",
            "",
            *table(outcome_columns, (tuple(map(inline, row)) for row in outcome_rows)),
            "## Medianas por modelo y etapa",
            "",
            *table(columns, (tuple(map(inline, row[:10])) for row in rows)),
            *notes,
            "",
            "## Corridas archivadas",
            "",
            *[
                f"- [{inline(run['label'])} · {inline(run['run'])}]({quote(relative(folder, path, 'resumen llm.md'))})"
                f" · {inline(status(decisions, issues))}"
                for path, run, decisions, issues in runs
            ],
        ],
    )
    total = [
        (f"{label} · {model}", value)
        for label, model, _, *_, value, score in rows
        if value is not None
    ]
    quality = [
        f"<section><h3>{escape(name)}</h3>"
        + bars(
            [
                (f"{label} · {model}", score)
                for label, model, stage, *_, score in rows
                if stage == name and score is not None
            ],
            "%",
            maximum=100,
        )
        + "</section>"
        for name in labels.values()
    ]
    links = [
        f"<li><a href='{escape(quote(relative(folder, path, 'resumen llm.md')))}'>"
        f"{escape(run['label'])} · {escape(run['run'])}</a> · {escape(status(decisions, issues))}</li>"
        for path, run, decisions, issues in runs
    ]
    template = Path(__file__).with_name("comparacion.html").read_text(encoding="utf-8")
    output = Template(template).substitute(
        title=escape(data["title"]),
        overview="".join(f"<p>{escape(line)}</p>" for line in overview),
        outcomes=html_table(outcome_columns, outcome_rows),
        tokens=bars(total, ""),
        quality="".join(quality),
        metrics=html_table(columns, (row[:10] for row in rows)),
        notes="".join(f"<li>{escape(note)}</li>" for note in notes),
        runs=("<ul>" + "".join(links) + "</ul>")
        if links
        else "<p>Todavía no hay corridas archivadas.</p>",
    )
    (folder / "comparacion.html").write_text(output, encoding="utf-8")


def relative(folder, path, name):
    return (path.relative_to(folder) / name).as_posix()


def status(review, issues):
    if issues:
        return "Fuera de la comparación. " + " ".join(issues)
    return (
        "Revisada"
        if review is not None
        else "Consumo medido. Revisión de calidad pendiente."
    )
