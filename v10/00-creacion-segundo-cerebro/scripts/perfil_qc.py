"""Contrato del perfil que separa el generador V3 de los datos de cada aplicación."""

from pathlib import PurePosixPath

from fichas import texto
from repositorio import ID

TIPOS_FUENTE = {"contrato", "implementacion", "configuracion", "test"}


def id_qc(value, campo):
    if not isinstance(value, str) or not ID.fullmatch(value) or value in {"index", "log"}:
        raise ValueError(f"{campo}: usá un ID en minúsculas con letras, números o guiones.")
    return value


def prefijo(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("Las rutas del perfil deben ser relativas al repositorio.")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError("Las rutas del perfil deben ser relativas al repositorio.")
    return path.as_posix()


def contiene(path, prefix):
    return path == prefix or path.startswith(prefix + "/")


def validar_perfil(value):
    required = {"aplicacion", "repositorio", "revision", "flujos_criticos", "fuentes"}
    optional = {"modulos", "exclusiones", "presupuesto", "linea_base_tokens"}
    if not isinstance(value, dict) or required - value.keys() or value.keys() - required - optional:
        raise ValueError("El perfil V3 requiere aplicación, repositorio, revisión, fuentes y flujos críticos.")
    app = texto(value["aplicacion"], 160, "aplicacion")
    revision = texto(value["revision"], 100, "revision Git")
    if not isinstance(value["repositorio"], str) or not value["repositorio"].strip():
        raise ValueError("Indicá la ruta del repositorio en el perfil.")
    flujos, fuentes = {}, {}
    for field in ("flujos_criticos", "fuentes"):
        if not isinstance(value[field], list) or not value[field]:
            raise ValueError(f"El perfil requiere al menos una entrada en {field}.")
    for item in value["flujos_criticos"]:
        if not isinstance(item, dict) or set(item) != {"id", "titulo", "riesgo"}:
            raise ValueError("Cada flujo crítico requiere id, titulo y riesgo.")
        key = id_qc(item["id"], "flujo")
        if key in flujos:
            raise ValueError(f"Flujo crítico duplicado: {key}.")
        flujos[key] = {"titulo": texto(item["titulo"], 110, "titulo"), "riesgo": texto(item["riesgo"], 240, "riesgo")}
    for source in value["fuentes"]:
        if not isinstance(source, dict) or set(source) != {"prefijo", "tipo"} or source["tipo"] not in TIPOS_FUENTE:
            raise ValueError("Cada fuente requiere prefijo y tipo contrato, implementacion, configuracion o test.")
        ruta = prefijo(source["prefijo"])
        if ruta in fuentes:
            raise ValueError(f"Prefijo de fuente duplicado: {ruta}.")
        fuentes[ruta] = source["tipo"]
    raw_exclusiones = value.get("exclusiones", [])
    if not isinstance(raw_exclusiones, list):
        raise ValueError("Las exclusiones son una lista de rutas relativas.")
    presupuesto = {"navegacion_caracteres": 7000, "recuperacion_caracteres": 16000, "portada_tokens": 800}
    raw = value.get("presupuesto", {})
    if not isinstance(raw, dict) or raw.keys() - presupuesto.keys():
        raise ValueError("Presupuesto de contexto inválido.")
    presupuesto.update(raw)
    for key, (lower, upper) in {
        "navegacion_caracteres": (800, 30000), "recuperacion_caracteres": (3000, 30000), "portada_tokens": (100, 4000)
    }.items():
        if type(presupuesto[key]) is not int or not lower <= presupuesto[key] <= upper:
            raise ValueError(f"{key}: indicá un entero entre {lower} y {upper}.")
    baseline = value.get("linea_base_tokens")
    if baseline is not None and (type(baseline) is not int or baseline <= 0):
        raise ValueError("La línea base de tokens debe ser un entero positivo.")
    return {
        "aplicacion": app, "revision": revision, "modulos": value.get("modulos", {}),
        "flujos_criticos": flujos, "fuentes": fuentes,
        "exclusiones": sorted({prefijo(p) for p in raw_exclusiones}), "presupuesto": presupuesto,
        **({"linea_base_tokens": baseline} if baseline is not None else {}),
    }
