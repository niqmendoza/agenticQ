"""Inventario local y contratos de respuesta para las suites de release."""

import json
import re
from pathlib import Path
from urllib.parse import unquote


def read_spec(path):
    path = Path(path)
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError:
            raise ValueError("Instalá el extra api para leer OpenAPI YAML.") from None
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            raise ValueError("El documento OpenAPI contiene YAML inválido.") from None
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(node, file, root, seen=()):
    if isinstance(node, list):
        return [resolve(item, file, root, seen) for item in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        ref = node["$ref"]
        if not isinstance(ref, str) or "://" in ref:
            raise ValueError("OpenAPI requiere referencias a archivos locales.")
        filename, _, pointer = ref.partition("#")
        target = (file.parent / unquote(filename)).resolve() if filename else file
        key = (target, pointer)
        if (
            not target.is_relative_to(root)
            or key in seen
            or (pointer and not pointer.startswith("/"))
        ):
            raise ValueError(
                f"Referencia OpenAPI fuera del contrato o recursiva: {ref}"
            )
        value = read_spec(target)
        for token in unquote(pointer).split("/")[1:]:
            name = token.replace("~1", "/").replace("~0", "~")
            try:
                value = value[int(name)] if isinstance(value, list) else value[name]
            except (ValueError, KeyError, IndexError, TypeError):
                raise ValueError(f"Referencia OpenAPI sin resolver: {ref}") from None
        if len(node) != 1:
            raise ValueError(
                "La validación de contratos con campos hermanos de $ref requiere revisión."
            )
        return resolve(value, target, root, (*seen, key))
    return {k: resolve(v, file, root, seen) for k, v in node.items()}


def operation_for(spec, case):
    method = case["http"]["method"].lower()
    path = case["http"]["path"].partition("?")[0]
    matches = []
    for template, operations in spec["paths"].items():
        pattern = "".join(
            "[^/]+" if part.startswith("{") else re.escape(part)
            for part in re.split(r"(\{[^{}]+\})", template)
        )
        if re.fullmatch(pattern, path) and method in operations:
            matches.append((template, operations[method]))
    exact = [item for item in matches if item[0] == path]
    choices = exact or matches
    if len(choices) != 1:
        raise ValueError(f"{case['id']}: operación ausente o ambigua en OpenAPI.")
    operation = choices[0][1]
    if (
        case.get("operation_id")
        and operation.get("operationId") != case["operation_id"]
    ):
        raise ValueError(f"{case['id']}: operationId difiere del contrato.")
    return operation


def response_schema(file, case, selector):
    spec = read_spec(file)
    if not str(spec.get("openapi", "")).startswith("3.1."):
        raise ValueError("La aserción de esquema requiere OpenAPI 3.1.")
    operation = operation_for(spec, case)
    key = str(selector["status"])
    responses = operation["responses"]
    response = (
        responses.get(key) or responses.get(key[0] + "XX") or responses.get("default")
    )
    if not response:
        raise ValueError(f"Falta la respuesta OpenAPI {key}.")
    response = resolve(response, file, file.parent)
    try:
        schema = response["content"][selector.get("media_type", "application/json")][
            "schema"
        ]
    except KeyError:
        raise ValueError(
            f"Respuesta {key} sin esquema para el tipo solicitado."
        ) from None
    schema_validator(schema)
    return schema


def schema_validator(schema):
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError:
        raise ValueError(
            "Instalá el extra api para validar el contrato JSON."
        ) from None

    def local(node):
        if isinstance(node, dict):
            if {"$ref", "$dynamicRef", "$recursiveRef"}.intersection(node):
                raise ValueError(
                    "La aserción necesita un esquema con referencias ya resueltas."
                )
            for child in node.values():
                local(child)
        elif isinstance(node, list):
            for child in node:
                local(child)

    local(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError:
        raise ValueError("El contrato contiene un esquema JSON inválido.") from None
    return Draft202012Validator(schema)
