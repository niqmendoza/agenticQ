"""Comparación de resultados V5 y V6 por identidad del caso."""

from collections import Counter
import re
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from audit import STATES
from markdown import inline, table
from release import case_digest
from session import read_json


def design_ids(folder):
    return {
        c["id"]: case_digest(c)
        for c in read_json(folder / "events.json")
        if c["kind"] == "case"
    }


def read_public(notes, cases):
    def header(label):
        match = re.search(r"^- " + label + r" · (.+)$", notes, re.MULTILINE)
        if not match:
            raise ValueError("El informe no tiene los metadatos esperados de V5.")
        return re.sub(r"\\(.)", r"\1", match[1])

    rows = {}
    for line in cases.split("### ", 1)[0].splitlines():
        if not line.startswith("| "):
            continue
        fields = [f.strip() for f in re.split(r"(?<!\\)\|", line[1:-1])]
        if len(fields) == 6 and fields[4] in STATES:
            key = re.sub(r"\\(.)", r"\1", fields[0])
            rows[key] = {
                "first": fields[3],
                "status": fields[4],
                "attempts": int(fields[5]),
            }
    return header("Versión o build"), header("Entorno"), rows, {}


def read_result(path):
    path = Path(path)
    if path.suffix.lower() == ".zip":
        try:
            with ZipFile(path) as bundle:
                matches = [
                    name
                    for name in bundle.namelist()
                    if name.endswith("/informe final.md")
                ]
                if len(matches) != 1:
                    raise ValueError("El ZIP requiere una sola entrega publicada.")
                folder = matches[0].rsplit("/", 1)[0]

                def read(name):
                    item = bundle.getinfo(folder + "/" + name)
                    if item.file_size > 32 * 1024 * 1024:
                        raise ValueError("El informe supera el tamaño admitido.")
                    return bundle.read(item).decode()

                if folder + "/resultado.json" in bundle.namelist():
                    import json

                    return structured(json.loads(read("resultado.json")))
                return read_public(read("informe final.md"), read("casos.md"))
        except BadZipFile:
            raise ValueError("ZIP inválido.") from None
    if path.is_dir() and (path / "resultado.json").exists():
        path = path / "resultado.json"
    if path.is_file():
        return structured(read_json(path))
    if (path / "informe final.md").exists():
        return read_public(
            (path / "informe final.md").read_text(), (path / "casos.md").read_text()
        )
    meta = read_json(path / "run.json")
    events = read_json(path / "events.json")
    rows = {
        c["id"]: {"first": "unattempted", "status": "unattempted", "attempts": 0}
        for c in events
        if c["kind"] == "case"
    }
    from contracts import validate_execution

    cases = {c["id"]: c for c in events if c["kind"] == "case"}
    for e in events:
        if e["kind"] == "execution":
            row = rows[e["case_id"]]
            state = e["status"]
            try:
                validate_execution(path, meta["profile"], cases[e["case_id"]], e)
            except (ValueError, OSError):
                state = "invalid_evidence"
            if row["attempts"] == 0:
                row["first"] = state
            row["status"] = state
            row["attempts"] += 1
    return meta["version"], meta["environment"], rows, design_ids(path)


def structured(data):
    if data.get("schema") != "agentic-qc/result-1":
        raise ValueError("Resultado de release desconocido.")
    return (
        data["build"],
        data["environment"],
        {r["case"]: r for r in data["cases"]},
        data["provenance"].get("cases", {}),
    )


def compare(args):
    a_build, a_env, left, a_ids = read_result(args.baseline)
    b_build, b_env, right, b_ids = read_result(args.candidate)
    same = (a_build, a_env) == (b_build, b_env)
    lines = [
        "# Comparación V5 y V6",
        "",
        f"- Base · {inline(a_build)} · {inline(a_env)}",
        f"- Candidata · {inline(b_build)} · {inline(b_env)}",
        "- Build y entorno · "
        + ("coinciden" if same else "diferentes, comparación descriptiva"),
        "- Confirmar el mismo estado inicial, actores y datos para atribuir diferencias al framework.",
        "",
        f"Casos comunes · {len(left.keys() & right.keys())}. Solo en la base · {len(left.keys() - right.keys())}. "
        f"Solo en la candidata · {len(right.keys() - left.keys())}.",
        "",
    ]

    def counts(items):
        counts = Counter(row["status"] for row in items.values())
        counts["pendientes"] = sum(
            counts[s] for s in ("partial", "not_run", "unattempted", "invalid_evidence")
        )
        counts["reintentos"] = sum(
            max(0, row["attempts"] - 1) for row in items.values()
        )
        return counts

    a_counts, b_counts = counts(left), counts(right)
    lines += table(
        ("Resultado en su alcance", "Base", "Candidata"),
        [
            (label, a_counts[state], b_counts[state])
            for state, label in (
                ("passed", "Aprobados"),
                ("failed", "Fallidos"),
                ("blocked", "Bloqueados"),
                ("pendientes", "Otros pendientes o sin evidencia válida"),
                ("reintentos", "Reintentos"),
            )
        ],
    )

    def status(row):
        return (
            f"{row['first']} → {row['status']} ({row['attempts']})"
            if row
            else "Ausente"
        )

    rows = []
    for key in sorted(left.keys() | right.keys()):
        design = "Sin par"
        if key in left and key in right:
            design = "Sin huella verificable"
            if key in a_ids and key in b_ids:
                design = "Igual" if a_ids[key] == b_ids[key] else "Modificado"
        rows.append(
            (inline(key), status(left.get(key)), status(right.get(key)), design)
        )
    lines += table(
        (
            "Caso",
            "Base · primero → último (intentos)",
            "Candidata · primero → último (intentos)",
            "Diseño",
        ),
        rows,
    )
    with Path(args.out).open("x", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")
    print(Path(args.out).resolve())
