"""Identificadores sintéticos compartidos por los pasos de un escenario."""

import re

TOKEN = re.compile(r"\{\{([A-Za-z_][A-Za-z_0-9]*)\}\}")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}")


def bind(value, variables):
    if isinstance(value, list):
        return [bind(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: bind(item, variables) for key, item in value.items()}
    if isinstance(value, str):

        def replace(match):
            key = match[1]
            if key not in variables:
                raise ValueError(f"Falta el identificador sintético {key}.")
            return variables[key]

        return TOKEN.sub(replace, value)
    return value


def bind_profile(profile, variables):
    # Una respuesta puede proporcionar un ID para una ruta relativa aprobada.
    # El origen, los actores, los selectores y las credenciales vienen del perfil.
    result = dict(profile)
    for field in ("browser_paths", "http_operations"):
        if field == "browser_paths":
            result[field] = [partial_path(p, variables) for p in profile.get(field, [])]
        else:
            result[field] = [
                {**op, "path": partial_path(op["path"], variables)}
                for op in profile.get(field, [])
            ]
    return result


def partial_path(path, variables):
    return TOKEN.sub(lambda m: variables.get(m[1], m[0]), path)
