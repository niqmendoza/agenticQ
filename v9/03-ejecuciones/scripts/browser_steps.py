"""Acciones Playwright ordenadas y comprobaciones visibles para recorridos funcionales."""

from hashlib import sha256
import os
from pathlib import Path
from time import perf_counter

from credenciales import ocultar


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
            not in ("click", "fill", "press", "select", "upload", "wait_visible", "wait_hidden", "download")
        ):
            raise ValueError("Cada paso requiere ID único, acción y control declarado.")
        identifiers.add(identifier)
        value = action.get("value")
        selector = controls[control]
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
        prepared.append((identifier, kind, selector, value, control))
    if not any(
        kind in ("click", "press", "upload", "select", "download") for _, kind, _, _, _ in prepared
    ):
        raise ValueError("El recorrido necesita una interacción que ejecute la tarea.")
    control_checks = {"control_visible", "control_text", "control_contains"}
    visible_checks = control_checks | {"visible_text", "download_file"}
    if not any(check["type"] in visible_checks for check in checks.values()):
        raise ValueError("El recorrido necesita comprobar un resultado visible.")
    for check in checks.values():
        if check["type"] in control_checks and (
            not isinstance(check.get("control"), str)
            or check["control"] not in controls
        ):
            raise ValueError("La comprobación requiere un control declarado.")
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


def verificar_descarga(descarga, check):
    coincide = (
        descarga["bytes"] >= check.get("min_bytes", 1)
        and descarga["extension"] == check["extension"].casefold()
    )
    return coincide, f"{descarga['extension']} · {descarga['bytes']} bytes · SHA-256 {descarga['sha256']}"


def perform_steps(
    page, steps, checks, controls, responses, browser_error, expect, *,
    timeout=15000, secretos=(),
):
    execution, downloads = [], {}
    for identifier, kind, selector, value, control in steps:
        tick = perf_counter()
        locator = page.locator(selector)
        action = {"id": identifier, "type": kind, "control": control, "outcome": "observed"}
        try:
            if kind == "click":
                locator.click(timeout=timeout)
            elif kind in ("wait_visible", "wait_hidden"):
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
                downloads[identifier] = action["descarga"] = {
                    "bytes": path.stat().st_size,
                    "extension": Path(download.suggested_filename).suffix.casefold(),
                    "sha256": digest.hexdigest(),
                }
        except (browser_error, OSError) as error:
            count = ocurrencias(locator, browser_error)
            action.update(outcome="action_error", coincidencias=count, causa=fallo_accion(error, count))
        action["duration_ms"] = round((perf_counter() - tick) * 1000)
        execution.append(action)
        if action["outcome"] == "action_error":
            return None, execution, {}

    verified, observed = {}, {}
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
            verified[identifier], observed[identifier] = verificar_descarga(downloads[check["step"]], check)
            continue
        locator = (
            page.get_by_text(expected, exact=True).first if kind == "visible_text"
            else page.locator(controls[check["control"]])
        )
        try:
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
                observed[identifier] = ocultar(text, secretos)[:500]
            except browser_error:
                observed[identifier] = "No se pudo leer el control."
        else:
            observed[identifier] = f"Control visible · {count} coincidencias." if verified[identifier] else f"Control no verificado · {count} coincidencias."
    return verified, execution, observed
