"""Comprobar prerrequisitos y separar los casos que dependen de cada uno."""

from importlib.util import find_spec
from pathlib import Path
from socket import create_connection
from time import perf_counter
from urllib.parse import urlsplit

from credenciales import referencias
from runners import Unavailable, playwright_browser


def probar_url(base_url):
    if not base_url:
        return "sin URL"
    url = urlsplit(base_url)
    try:
        with create_connection((url.hostname, url.port or (443 if url.scheme == "https" else 80)), timeout=3):
            return "TCP accesible"
    except OSError:
        return "TCP inaccesible"


def comprobar(casos, manifiesto, perfil, entorno):
    start = perf_counter()
    por_caso = {case["id"]: case for case in casos}
    metodos = {item["via"] for item in manifiesto}
    navegador = "no solicitado"
    navegador_error = None
    if "playwright" in metodos:
        try:
            with playwright_browser(perfil):
                navegador = "iniciado"
        except (Unavailable, OSError) as error:
            navegador, navegador_error = "bloqueado", str(error)
    url = probar_url(perfil.get("base_url")) if metodos & {"http", "api", "playwright"} else "no solicitada"
    requeridas = set()
    ausentes = set()
    bloqueos = {}
    for paso in manifiesto:
        clave, via = paso["case"], paso["via"]
        caso = por_caso[clave]
        nombres = referencias(caso, paso, perfil)
        requeridas.update(nombres)
        faltantes = sorted(n for n in nombres if not entorno.get(n))
        ausentes.update(faltantes)
        causas = []
        if faltantes:
            causas.append("Variables de credenciales ausentes · " + ", ".join(faltantes))
        if via == "playwright" and navegador_error:
            causas.append(navegador_error)
        if via in ("playwright", "http", "api") and url != "TCP accesible":
            causas.append(f"URL del perfil · {url}.")
        if via == "api" and find_spec("playwright") is None:
            causas.append("El canal api usa Playwright para Python.")
        if via == "playwright" and caso.get("browser_flow") == "web_ui" and any(
            c.get("check", {}).get("type") == "visible_text" for c in caso["criteria"]
        ):
            causas.append("Migrá visible_text a un control de resultado específico en el diseño.")
        if via == "db":
            db = perfil["database"]
            if db["driver"] == "postgres" and find_spec("psycopg") is None:
                causas.append("Falta el driver de PostgreSQL.")
            elif db["driver"] == "sqlite" and not Path(db["path"]).is_file():
                causas.append("Falta el archivo SQLite aprobado.")
        dependencias = [dep for dep in paso.get("depends_on", []) if dep in bloqueos]
        if dependencias:
            causas.append("Dependencias bloqueadas · " + ", ".join(dependencias))
        if causas:
            bloqueos[clave] = " ".join(causas)
    return {
        "duracion_tecnica_ms": round((perf_counter() - start) * 1000),
        "navegador_requerido": "playwright" in metodos,
        "navegador": navegador,
        "url_conectividad": url,
        "variables_requeridas": sorted(requeridas),
        "variables_ausentes": sorted(ausentes),
        "bloqueos_por_caso": bloqueos,
        **({"motivo": navegador_error} if navegador_error else {}),
    }
