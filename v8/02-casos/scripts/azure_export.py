"""Exporta el diseño de casos al CSV de Azure Test Plans."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from session import ROOT, TEMPLATES, load, run_id

AZURE = ROOT / "azure"
HEADERS = (
    "ID",
    "Work Item Type",
    "Title",
    "Test Step",
    "Step Action",
    "Step Expected",
    "Area Path",
    "Assigned To",
    "State",
    "Tipo de caso de prueba",
    "Funcionalidad",
    "Tipo de componente",
    "Tipo",
)


def cell(value):
    # Conserva los saltos internos y evita fórmulas al abrir el CSV en una planilla.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def case_rows(case, area, assigned_to, state):
    azure = case.get("azure", {})
    actions = case["steps"]
    expected = case.get("step_expected")
    if expected is None:
        expected = [""] * (len(actions) - 1) + [case["expected"]]
    steps = list(zip(actions, expected))
    if case["preconditions"]:
        preconditions = "\n".join(f"- {item}" for item in case["preconditions"])
        steps.insert(0, ("Precondiciones:\n" + preconditions, ""))
    metadata = (
        area,
        assigned_to,
        state,
        azure.get("test_case_type", ""),
        azure.get("functionality", case["feature"]),
        azure.get("component_type", "API" if case["level"].casefold() == "api" else ""),
        azure.get("type", "Functional"),
    )
    work_item = azure.get("work_item_id", "")
    if work_item != "" and (type(work_item) is not int or work_item < 1):
        raise ValueError("work_item_id debe ser un ID positivo de Azure.")
    for number, (action, result) in enumerate(steps, 1):
        yield (
            work_item,
            "Test Case",
            case["title"].strip(),
            number,
            action,
            result,
            *metadata,
        )


def export_azure(args):
    run, _, events = load(args.run)
    area, assigned_to, state = (
        args.area.strip(),
        args.assigned_to.strip(),
        args.state.strip(),
    )
    if not area or not state:
        raise ValueError("Indicá una ruta de área y un estado de Azure.")
    cases = [event for event in events if event["kind"] == "case"]
    if not cases:
        raise ValueError("Registrá al menos un caso antes de exportar a Azure.")
    if getattr(args, "case", None):
        keys = set(args.case)
        missing = keys - {c["id"] for c in cases}
        if missing:
            raise ValueError(f"Casos desconocidos: {', '.join(sorted(missing))}")
        cases = [c for c in cases if c["id"] in keys]
    mapped = [
        case.get("azure", {}).get("work_item_id")
        for case in cases
        if "work_item_id" in case.get("azure", {})
    ]
    if len(set(mapped)) != len(mapped):
        raise ValueError("Hay más de un caso asignado al mismo work item de Azure.")
    titles = set()
    for case in cases:
        title = cell(case["title"].strip())
        normalized = title.casefold()
        if normalized in titles:
            raise ValueError(f"Título de Azure duplicado en el caso {case['id']}.")
        if len(title) > 128:
            raise ValueError(
                f"El título de {case['id']} supera 128 caracteres para Azure."
            )
        titles.add(normalized)

    target = AZURE / f"{run_id(args.name or run.name)}.csv"
    if AZURE.is_symlink():
        raise ValueError("azure debe ser una carpeta local a V6.")
    if target.exists() or target.is_symlink():
        raise ValueError("El CSV ya existe. Usá --name para exportar una revisión.")
    with (TEMPLATES / "azure-test-cases.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source:
        fields = next(csv.reader(source), [])
    if len(fields) != len(HEADERS) or set(fields) != set(HEADERS):
        raise ValueError(
            "Revisá los encabezados obligatorios de la plantilla CSV para Azure."
        )
    AZURE.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=AZURE) as temporary:
        draft = Path(temporary) / target.name
        with draft.open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for case in cases:
                for row in case_rows(case, area, assigned_to, state):
                    writer.writerow(
                        {key: cell(value) for key, value in zip(HEADERS, row)}
                    )
        draft.rename(target)
    print(target)
