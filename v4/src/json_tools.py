"""Aserciones y variantes de fixtures JSON para pruebas de contrato."""

import json
from pathlib import Path

from session import read_json


JSON_TYPES = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "object": (dict,),
    "array": (list,),
    "null": (type(None),),
}


def valid_path(path):
    return (
        isinstance(path, list)
        and bool(path)
        and all(isinstance(key, str) or type(key) is int and key >= 0 for key in path)
    )


def json_at(data, path):
    for key in path:
        if (isinstance(key, str) and isinstance(data, dict)) or (
            type(key) is int and isinstance(data, list)
        ):
            data = data[key]
        else:
            raise KeyError(key)
    return data


def fixture_variant(args):
    fixture = read_json(args.fixture)
    path, replacement = json.loads(args.path), json.loads(args.value)
    if not valid_path(path):
        raise ValueError(
            "--path debe ser una lista JSON de claves o índices no negativos."
        )
    try:
        original = json_at(fixture, path)
    except (KeyError, IndexError):
        raise ValueError("El campo debe existir en el fixture original.") from None
    if type(original) is type(replacement):
        raise ValueError("El nuevo valor debe tener un tipo distinto del original.")
    parent = json_at(fixture, path[:-1])
    parent[path[-1]] = replacement
    payload = json.dumps(fixture, ensure_ascii=False, indent=2, allow_nan=False)
    output = Path(args.out)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(payload + "\n")
    print(output)
