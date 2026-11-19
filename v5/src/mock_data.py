"""Crea fixtures JSON reproducibles a partir de campos definidos por QA."""

import json
from pathlib import Path
from random import Random
from uuid import UUID

from session import load, read_json, run_id


def mock_values(spec, random):
    if not isinstance(spec, dict) or not spec:
        raise ValueError("El esquema debe asociar campos con generadores.")
    generators = {}
    for name, field in spec.items():
        if not name.strip() or not isinstance(field, dict):
            raise ValueError("Cada campo requiere una definición.")
        kind = field.get("type")
        if kind == "constant" and "value" in field:
            generators[name] = lambda _index, value=field["value"]: value
        elif (
            kind == "choice"
            and isinstance(field.get("values"), list)
            and field["values"]
        ):
            generators[name] = lambda _index, values=field["values"]: random.choice(
                values
            )
        elif (
            kind == "integer"
            and type(field.get("min")) is int
            and type(field.get("max")) is int
            and field["min"] <= field["max"]
        ):
            generators[name] = lambda _index, lower=field["min"], upper=field["max"]: (
                random.randint(lower, upper)
            )
        elif kind == "boolean":
            generators[name] = lambda _index: bool(random.getrandbits(1))
        elif kind == "uuid":
            generators[name] = lambda _index: str(
                UUID(int=random.getrandbits(128), version=4)
            )
        elif kind == "sequence" and isinstance(field.get("prefix", "QA-"), str):
            generators[name] = lambda index, prefix=field.get("prefix", "QA-"): (
                f"{prefix}{index}"
            )
        else:
            raise ValueError(f"Generador inválido para {name}.")
    return generators


def generate_mock_data(args):
    run, _, _ = load(args.run)
    if not 1 <= args.count <= 1000:
        raise ValueError("La cantidad de registros debe estar entre 1 y 1000.")
    generators = mock_values(read_json(Path(args.spec)), Random(args.seed))
    rows = [
        {name: generate(index) for name, generate in generators.items()}
        for index in range(1, args.count + 1)
    ]
    output = rows[0] if args.count == 1 else rows
    text = json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False)
    fixtures = run / "fixtures"
    if fixtures.is_symlink():
        raise ValueError("fixtures/ debe ser una carpeta local de la corrida.")
    fixtures.mkdir(exist_ok=True)
    target = fixtures / f"{run_id(args.name)}.json"
    with target.open("x", encoding="utf-8") as stream:
        stream.write(text + "\n")
    print(target)
