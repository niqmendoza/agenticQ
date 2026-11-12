"""Auditoría de cobertura y evidencia a partir del registro de una sesión V4."""

from collections import Counter

from contracts import validate_execution
from session import load, read_json, write_json


def audit(args):
    run, meta, events = load(args.run)
    if meta["schema"] != "qa-run/2":
        raise ValueError("audit requiere una sesión V4 con perfil.")
    cases = {event["id"]: event for event in events if event["kind"] == "case"}
    latest = {
        event["case_id"]: event for event in events if event["kind"] == "execution"
    }
    inventory = None
    if args.requirements:
        inventory = read_json(args.requirements)
        if (
            not isinstance(inventory, list)
            or not inventory
            or not all(isinstance(item, str) and item.strip() for item in inventory)
            or len(set(inventory)) != len(inventory)
        ):
            raise ValueError("El catálogo debe ser una lista de IDs únicos no vacíos.")

    by_requirement = {}
    issues = []
    counts = Counter()
    for case_id, case in cases.items():
        attempt = latest.get(case_id)
        status = attempt["status"] if attempt else "unattempted"
        if attempt:
            try:
                validate_execution(run, meta["profile"], case, attempt)
            except ValueError as error:
                issues.append({"case_id": case_id, "issue": str(error)})
                status = "invalid_evidence"
        counts[status] += 1
        by_requirement.setdefault(case["requirement"], []).append(
            {"case_id": case_id, "status": status}
        )

    planned = set(by_requirement)
    approved = {
        requirement
        for requirement, linked_cases in by_requirement.items()
        if all(case["status"] == "passed" for case in linked_cases)
    }
    catalog = set(inventory) if inventory is not None else None
    report = {
        "case_status": dict(counts),
        "requirements": by_requirement,
        "catalog_size": len(catalog) if catalog is not None else None,
        "catalog_without_cases": (
            sorted(catalog - planned) if catalog is not None else None
        ),
        "catalog_with_all_linked_cases_passed": (
            sorted(catalog & approved) if catalog is not None else None
        ),
        "case_requirements_outside_catalog": (
            sorted(planned - catalog) if catalog is not None else None
        ),
        "inferred_cases": [
            case_id
            for case_id, case in cases.items()
            if case["oracle_status"] == "inferred"
        ],
        "evidence_issues": issues,
        "scope": "Valida estado y archivos del último intento. La pertinencia y el contenido de la evidencia requieren revisión.",
    }
    output = run / "audit.json"
    write_json(output, report)
    print(output)
    return 1 if issues else 0
