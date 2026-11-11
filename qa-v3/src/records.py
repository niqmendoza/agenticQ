"""Validación y registro de casos, ejecuciones y hallazgos."""

from session import load, read_json, render, timestamp, write_json

STATUSES = {"passed", "failed", "blocked", "not_run"}
KINDS = {"case", "execution", "finding", "note"}


def validate_record(item, case_ids, finding_ids):
    if (
        not isinstance(item, dict)
        or not isinstance(item.get("kind"), str)
        or item["kind"] not in KINDS
    ):
        raise ValueError(
            "Cada registro debe ser un objeto con kind: case, execution, finding o note."
        )
    if "time_utc" in item:
        raise ValueError(
            "time_utc lo asigna el sistema; usar otro campo para la hora observada."
        )
    kind = item["kind"]
    required = {
        "case": ("id", "title", "expected", "oracle_status", "sources"),
        "execution": ("case_id", "status", "observation", "evidence"),
        "finding": ("id", "observation", "evidence", "interpretation", "pending"),
        "note": ("phase", "observation"),
    }[kind]
    if any(key not in item or item[key] in ("", None, []) for key in required):
        raise ValueError("Faltan campos obligatorios: " + ", ".join(required))
    for key in ("id", "case_id"):
        if key in item and (not isinstance(item[key], str) or not item[key].strip()):
            raise ValueError(f"{key} debe ser un texto no vacío.")
    if (kind == "case" and item["id"] in case_ids) or (
        kind == "finding" and item["id"] in finding_ids
    ):
        raise ValueError("ID duplicado para este tipo de registro.")
    if kind == "case" and item["oracle_status"] not in (
        "documented",
        "inferred",
        "pending",
    ):
        raise ValueError("oracle_status debe ser documented, inferred o pending.")
    if kind == "execution":
        if not isinstance(item["status"], str) or item["status"] not in STATUSES:
            raise ValueError("Estado de ejecución inválido.")
        if item["case_id"] not in case_ids:
            raise ValueError("La ejecución debe referir a un caso registrado.")


def record(args):
    run, _, events = load(args.run)
    data = read_json(args.json)
    items = data if isinstance(data, list) else [data]
    if not items:
        raise ValueError("La lista de registros no puede estar vacía.")
    case_ids = {event["id"] for event in events if event["kind"] == "case"}
    finding_ids = {event["id"] for event in events if event["kind"] == "finding"}
    # Validar el lote completo antes de escribir: ningún evento parcial si hay errores.
    for item in items:
        validate_record(item, case_ids, finding_ids)
        events.append({"time_utc": timestamp(), **item})
        if item["kind"] == "case":
            case_ids.add(item["id"])
        elif item["kind"] == "finding":
            finding_ids.add(item["id"])
    write_json(run / "events.json", events)
    render(run)
    print(run / "log.md")
