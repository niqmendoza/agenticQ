"""Acciones Playwright ordenadas y comprobaciones visibles para recorridos funcionales."""

from hashlib import sha256
import os
from pathlib import Path
from time import perf_counter
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree

from credenciales import ocultar
from higiene import sanear


class BrowserDataUnavailable(Exception):
    pass


def prepare_steps(case, profile, run, checks, *, environment=None):
    if environment is None:
        environment = os.environ
    actions = case.get("browser_steps")
    if not isinstance(actions, list) or not actions:
        raise ValueError(
            "El recorrido necesita browser_steps o una ejecución Playwright externa registrada."
        )
    controls = profile.get("browser_controls", {})
    prepared = []
    identifiers = set()
    scopes = {}
    for action in actions:
        if not isinstance(action, dict):
            raise ValueError("Cada paso de navegador debe ser un objeto.")
        identifier, control = action.get("id"), action.get("control")
        kind = action.get("type")
        if (
            not isinstance(identifier, str)
            or not identifier.strip()
            or identifier in identifiers
            or not isinstance(control, str)
            or control not in controls
            or kind
            not in ("click", "fill", "press", "select", "upload", "wait_visible", "wait_hidden",
                    "download", "capture_count", "verify_model")
        ):
            raise ValueError("Cada paso requiere ID único, acción y control declarado.")
        identifiers.add(identifier)
        value = action.get("value")
        selector = controls[control]
        scope = action.get("scope")
        if scope is not None and (not isinstance(scope, str) or scope not in scopes):
            raise ValueError("scope debe indicar un capture_count anterior.")
        if kind == "capture_count":
            if scope is not None:
                raise ValueError("capture_count requiere un control sin scope.")
            scopes[identifier] = control
        if kind == "verify_model" and (
            not isinstance(value, str) or not value.strip()
            or action.get("property", "text") not in ("text", "value")
        ):
            raise ValueError("verify_model requiere un valor exacto y property text o value.")
        if kind == "fill" and "value_env" not in action and (
            'password' in control.casefold() or 'password' in selector.casefold()
        ):
            raise ValueError("El campo de contraseña requiere value_env.")
        if "value_env" in action:
            variable = action["value_env"]
            if (
                kind != "fill"
                or "value" in action
                or not isinstance(variable, str)
                or not variable.isidentifier()
            ):
                raise ValueError(
                    "value_env se usa para completar un campo desde una variable."
                )
            value = environment.get(variable)
            if not value:
                raise BrowserDataUnavailable(
                    f"Falta la variable para completar el paso {identifier}."
                )
        if kind in ("fill", "press", "select", "upload") and not isinstance(value, str):
            raise ValueError(f"Falta un valor para el paso {identifier}.")
        if kind == "upload":
            fixtures = run / "fixtures"
            source = (fixtures / value).resolve()
            if (
                Path(value).is_absolute()
                or fixtures.is_symlink()
                or fixtures not in source.parents
            ):
                raise ValueError(
                    "El archivo de prueba debe estar dentro de fixtures/ de la corrida."
                )
            if not source.is_file():
                raise BrowserDataUnavailable(
                    f"Falta el archivo de prueba para el paso {identifier}."
                )
            value = str(source)
        prepared.append((identifier, kind, selector, value, control, scope, action.get("property", "text")))
    if not any(
        step[1] in ("click", "press", "upload", "select", "download") for step in prepared
    ):
        raise ValueError("El recorrido necesita una interacción que ejecute la tarea.")
    control_checks = {"control_visible", "control_text", "control_contains", "control_absent"}
    visible_checks = control_checks | {"visible_text", "download_file"}
    if not any(check["type"] in visible_checks for check in checks.values()):
        raise ValueError("El recorrido necesita comprobar un resultado visible.")
    for check in checks.values():
        if check["type"] in control_checks and (
            not isinstance(check.get("control"), str)
            or check["control"] not in controls
        ):
            raise ValueError("La comprobación requiere un control declarado.")
        if "scope" in check and (
            check["type"] not in control_checks
            or not isinstance(check["scope"], str) or check["scope"] not in scopes
        ):
            raise ValueError("El scope de un criterio debe indicar un capture_count del caso.")
        if check["type"] == "download_file" and check["step"] not in {
            step[0] for step in prepared if step[1] == "download"
        }:
            raise ValueError("La comprobación de descarga requiere el ID de un paso download.")
    return prepared


def ocurrencias(locator, browser_error):
    try:
        return locator.count()
    except browser_error:
        return None


def fallo_accion(error, coincidencias):
    if coincidencias is not None and coincidencias > 1:
        return "selector_ambiguo"
    if "strict mode violation" in str(error).lower():
        return "selector_ambiguo"
    if coincidencias == 0 and type(error).__name__ == "TimeoutError":
        return "control_ausente"
    if type(error).__name__ == "TimeoutError":
        return "timeout"
    return "accion_no_completada"


TEXT_FORMATS = {".txt", ".md", ".csv", ".json", ".html", ".xml", ".tsv"}
XML_PARTS = {".docx": ("word/document.xml",), ".xlsx": ("xl/worksheets/sheet1.xml", "xl/sharedStrings.xml")}
MAX_INSPECTION = 8 * 1024 * 1024


def contenido_descarga(path, extension):
    if extension in TEXT_FORMATS:
        with path.open("rb") as stream:
            data = stream.read(MAX_INSPECTION + 1)
        if len(data) > MAX_INSPECTION:
            raise ValueError("contenido_supera_limite")
        return data.decode("utf-8-sig")
    if extension in XML_PARTS:
        parts = []
        with ZipFile(path) as archive:
            members = set(archive.namelist())
            for name in XML_PARTS[extension]:
                if name not in members:
                    if name.endswith("sharedStrings.xml"):
                        continue
                    raise ValueError("estructura_invalida")
                if archive.getinfo(name).file_size > MAX_INSPECTION:
                    raise ValueError("contenido_supera_limite")
                root = ElementTree.fromstring(archive.read(name))
                parts.extend(root.itertext())
        return "\n".join(parts)
    raise ValueError("formato_sin_lector")


def verificar_descarga(descarga, path, check):
    coincide = (
        descarga["bytes"] >= check.get("min_bytes", 1)
        and descarga["extension"] == check["extension"].casefold()
    )
    summary = f"{descarga['extension']} · {descarga['bytes']} bytes · SHA-256 {descarga['sha256']}"
    markers = check.get("contains", [])
    if markers and coincide:
        try:
            content = contenido_descarga(path, descarga["extension"])
        except (OSError, UnicodeError, BadZipFile, ElementTree.ParseError):
            return False, summary + " · contenido ilegible"
        except ValueError as error:
            return False, summary + " · " + str(error)
        matches = sum(marker in content for marker in markers)
        return matches == len(markers), f"{summary} · contenido {matches}/{len(markers)}"
    return coincide, summary


def locator_for(page, selector, control, scope, snapshots, *, root_only=False):
    if scope is None:
        return page.locator(selector)
    base, name, index = snapshots[scope]
    turn = page.locator(base).nth(index)
    return turn if root_only or control == name else turn.locator(selector)


def login_causa(status):
    return {
        400: "login_solicitud_invalida",
        401: "credenciales_rechazadas",
        403: "acceso_denegado",
        429: "limite_login",
    }.get(status, "login_servidor" if status >= 500 else "login_respuesta_inesperada")


def perform_steps(
    page, steps, checks, controls, responses, browser_error, expect, *,
    timeout=15000, secretos=(), login=None, login_response=None, timings=None,
):
    execution, downloads, snapshots = [], {}, {}
    for identifier, kind, selector, value, control, scope, property_name in steps:
        tick = perf_counter()
        locator = locator_for(page, selector, control, scope, snapshots)
        action = {"id": identifier, "type": kind, "control": control, "outcome": "observed"}
        try:
            if kind == "click":
                if login and identifier == login["step"]:
                    action["login"] = {"method": login["method"], "path": url_path(login["path"]), "status": None}
                    action["causa"] = "login_sin_respuesta"
                    with page.expect_response(login_response, timeout=timeout) as response:
                        locator.click(timeout=timeout)
                    status = response.value.status
                    action["login"]["status"] = status
                    action.pop("causa")
                    expected_status = login.get("status")
                    if (status != expected_status if expected_status is not None else not 200 <= status < 300):
                        action.update(outcome="action_error", causa=login_causa(status))
                else:
                    locator.click(timeout=timeout)
            elif kind == "capture_count":
                snapshots[identifier] = (selector, control, locator.count())
                action["coincidencias"] = snapshots[identifier][2]
            elif kind == "verify_model":
                expect(locator).to_be_visible(timeout=timeout)
                if property_name == "value":
                    expect(locator).to_have_value(value, timeout=timeout)
                else:
                    expect(locator).to_have_text(value, timeout=timeout)
            elif kind in ("wait_visible", "wait_hidden"):
                if scope is not None:
                    locator_for(page, "", "", scope, snapshots, root_only=True).wait_for(state="visible", timeout=timeout)
                locator.wait_for(state="visible" if kind == "wait_visible" else "hidden", timeout=timeout)
            elif kind == "fill":
                locator.fill(value, timeout=timeout)
            elif kind == "press":
                locator.press(value, timeout=timeout)
            elif kind == "select":
                locator.select_option(value, timeout=timeout)
            elif kind == "upload":
                locator.set_input_files(value, timeout=timeout)
            else:
                with page.expect_download(timeout=timeout) as recepcion:
                    locator.click(timeout=timeout)
                download = recepcion.value
                path = download.path()
                digest = sha256()
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                action["descarga"] = {
                    "bytes": path.stat().st_size,
                    "extension": Path(download.suggested_filename).suffix.casefold(),
                    "sha256": digest.hexdigest(),
                }
                downloads[identifier] = (action["descarga"], path)
        except (AssertionError, browser_error, OSError) as error:
            count = ocurrencias(locator, browser_error)
            cause = "modelo_no_verificado" if kind == "verify_model" else action.get("causa", fallo_accion(error, count))
            action.update(outcome="action_error", coincidencias=count, causa=cause)
        action["duration_ms"] = round((perf_counter() - tick) * 1000)
        execution.append(action)
        if action["outcome"] == "action_error":
            return None, execution, {}

    verified, observed = {}, {}
    checks_started = perf_counter()
    for identifier, check in sorted(
        checks.items(), key=lambda item: item[1]["type"] == "network_status"
    ):
        kind = check["type"]
        expected = check.get("equals")
        if kind == "network_status":
            observed[identifier] = f"HTTP de operación · {responses[-1]}" if responses else "Operación sin respuesta observada."
            verified[identifier] = bool(responses) and responses[-1] == expected
            continue
        if kind == "download_file":
            verified[identifier], observed[identifier] = verificar_descarga(*downloads[check["step"]], check)
            continue
        locator = (
            page.get_by_text(expected, exact=True).first if kind == "visible_text"
            else locator_for(page, controls[check["control"]], check["control"], check.get("scope"), snapshots)
        )
        try:
            if check.get("scope"):
                expect(locator_for(page, "", "", check["scope"], snapshots, root_only=True)).to_be_visible(timeout=timeout)
            if kind == "control_absent":
                expect(locator).to_have_count(0, timeout=timeout)
            else:
                expect(locator).to_be_visible(timeout=timeout)
            if kind == "control_text":
                expect(locator).to_have_text(expected, timeout=timeout)
            elif kind == "control_contains":
                expect(locator).to_contain_text(expected, timeout=timeout)
        except (AssertionError, browser_error):
            verified[identifier] = False
        else:
            verified[identifier] = True
        count = ocurrencias(locator, browser_error)
        if kind in ("control_text", "control_contains") and count == 1:
            try:
                text = locator.inner_text(timeout=min(timeout, 1000))
                observed[identifier] = sanear(ocultar(text, secretos))[0][:500]
            except browser_error:
                observed[identifier] = "No se pudo leer el control."
        else:
            observed[identifier] = f"Control · {count} coincidencias."
    if timings is not None:
        timings["checks_ms"] = round((perf_counter() - checks_started) * 1000)
    return verified, execution, observed


def url_path(path):
    return path.split("?", 1)[0]
