"""Contrato de alcance compartido entre las etapas."""

import re
import unicodedata

from session import run_id

SUPERFICIES = {"frontend", "api", "db"}


def texto(datos, clave):
    if not isinstance(datos, dict):
        raise ValueError("Cada recorrido requiere un objeto JSON.")
    valor = datos.get(clave)
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"Completá {clave} con texto.")
    return valor.strip()


def normalizar(encargo):
    if not isinstance(encargo, dict):
        raise ValueError("El encargo requiere un objeto JSON.")
    for campo in ("app", "entorno", "build"):
        encargo[campo] = texto(encargo, campo)
    if "app_id" in encargo:
        try:
            encargo["app_id"] = run_id(texto(encargo, "app_id"))
        except ValueError as error:
            raise ValueError("app_id es técnico. Usá letras ASCII, números, guiones o guiones bajos.") from error
    else:
        nombre = unicodedata.normalize("NFKD", encargo["app"]).encode("ascii", "ignore").decode()
        encargo["app_id"] = re.sub(r"[^a-zA-Z0-9_-]+", "-", nombre).strip("-_")[:80] or "aplicacion"
    recorridos = encargo.get("recorridos")
    if not isinstance(recorridos, list) or not recorridos:
        raise ValueError("El encargo requiere al menos un recorrido.")
    ids = set()
    pedido = set()
    for recorrido in recorridos:
        clave = run_id(texto(recorrido, "id"))
        if clave in ids:
            raise ValueError(f"ID de recorrido repetido: {clave}.")
        ids.add(clave)
        texto(recorrido, "objetivo")
        if "consulta" in recorrido:
            texto(recorrido, "consulta")
        superficie = texto(recorrido, "superficie").lower()
        if superficie not in SUPERFICIES:
            raise ValueError(f"{clave}: superficie debe ser frontend, api o db.")
        recorrido["superficie"] = superficie
        pedido.add(superficie)
        if "grupo" in recorrido:
            run_id(texto(recorrido, "grupo"))
    declaradas = encargo.get("superficies", sorted(pedido))
    if isinstance(declaradas, str):
        declaradas = ["frontend", "api"] if declaradas.strip().lower() == "ambas" else [declaradas]
    if not isinstance(declaradas, list) or not all(isinstance(s, str) for s in declaradas):
        raise ValueError("superficies admite frontend, api, ambas o una lista de superficies.")
    declaradas = [s.strip().lower() for s in declaradas]
    if set(declaradas) != pedido or len(set(declaradas)) != len(declaradas):
        raise ValueError("superficies debe coincidir con los recorridos. Usá IDs separados para frontend y API.")
    encargo["superficies"] = sorted(pedido)
    prioridades = encargo.get("recorridos_priorizados", [])
    if (
        not isinstance(prioridades, list)
        or not all(isinstance(clave, str) and clave in ids for clave in prioridades)
        or len(set(prioridades)) != len(prioridades)
    ):
        raise ValueError("recorridos_priorizados debe listar IDs únicos del encargo.")
    for campo in ("modo_auth_esperado", "area_qa", "build_ref"):
        if campo in encargo:
            encargo[campo] = texto(encargo, campo)
    return encargo
