"""Puntúa suites generadas sobre un build sano y regresiones funcionales conocidas."""

from pathlib import Path
from statistics import median
from collections import defaultdict

from markdown import inline, table
from session import read_json, run_id


def score_models(args):
    config_path = Path(args.experiment).resolve()
    config = read_json(config_path)
    data = config["trials"]
    expected = config["regressions"]
    if (
        not isinstance(data, list)
        or not data
        or not isinstance(expected, dict)
        or not expected
    ):
        raise ValueError(
            "El experimento requiere repeticiones y regresiones conocidas."
        )
    groups = defaultdict(list)
    seen = set()
    files_seen = set()
    for trial in data:
        model, repetition = trial["model"], run_id(trial["id"])
        if (model, repetition) in seen:
            raise ValueError("Repetición duplicada.")
        seen.add((model, repetition))
        if trial.get("incomplete"):
            groups[model].append(None)
            continue
        selected = trial["results"]
        if set(selected) != {"healthy", *expected}:
            raise ValueError(
                "Cada repetición necesita la versión sana y todos los builds alternativos."
            )
        results = {}
        for build, file in selected.items():
            path = (config_path.parent / file).resolve()
            if path in files_seen:
                raise ValueError("El experimento reutiliza una corrida.")
            files_seen.add(path)
            result = read_json(path)
            required_build = (
                config["healthy_build"]
                if build == "healthy"
                else expected[build]["build"]
            )
            if (
                result["schema"] != "agentic-qc/result-1"
                or result["build"] != required_build
                or result["environment"] != config["environment"]
                or result["provenance"]["app"] != config["app"]
            ):
                raise ValueError(
                    "Los resultados difieren de los builds, entorno o aplicación fijados."
                )
            results[build] = result
        if (
            len(
                {
                    (r["provenance"]["suite"], r["provenance"]["profile"])
                    for r in results.values()
                }
            )
            != 1
        ):
            raise ValueError(
                "Cada modelo debe ejecutar su misma suite y perfil en todos los builds."
            )
        statuses = {
            b: {c["case"]: c["status"] for c in r["cases"]} for b, r in results.items()
        }
        if any(
            r["issues"] or r["missing_requirements"] or not r["cases"]
            for r in results.values()
        ) or any(
            status not in ("passed", "failed")
            for rows in statuses.values()
            for status in rows.values()
        ):
            groups[model].append(None)
            continue
        healthy = statuses["healthy"]
        # El revisor vincula casos al defecto conocido y revisa el motivo del fallo.
        detected = 0
        links = trial["reviewed_cases"]
        if set(links) != set(expected):
            raise ValueError(
                "Falta la revisión independiente de una regresión conocida."
            )
        for defect in expected:
            ids = links[defect]
            if not isinstance(ids, list) or any(
                key not in healthy or key not in statuses[defect] for key in ids
            ):
                raise ValueError(
                    "El revisor debe indicar casos existentes en los dos builds."
                )
            detected += any(
                healthy[key] == "passed" and statuses[defect][key] == "failed"
                for key in ids
            )
        groups[model].append(
            (
                100 * detected / len(expected),
                100 * sum(s == "failed" for s in healthy.values()) / len(healthy),
            )
        )
    rows = []
    for model, trials in sorted(groups.items()):
        valid = [row for row in trials if row is not None]
        rows.append(
            (
                inline(model),
                f"{len(valid)}/{len(trials)}",
                f"{median(row[0] for row in valid):.1f}%" if valid else "—",
                f"{median(row[1] for row in valid):.1f}%" if valid else "—",
            )
        )
    out = Path(args.out)
    with out.open("x", encoding="utf-8") as file:
        file.write(
            "\n".join(
                [
                    "# Detección de regresiones conocidas",
                    "",
                    "Medianas por repetición. Los casos fallidos del build sano requieren revisión.",
                    "",
                    *table(
                        (
                            "Modelo declarado",
                            "Evaluables / iniciadas",
                            "Regresiones detectadas",
                            "Casos fallidos en build sano",
                        ),
                        rows,
                    ),
                ]
            )
        )
    print(out.resolve())
