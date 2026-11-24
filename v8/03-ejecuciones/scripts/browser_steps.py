"""Acciones Playwright ordenadas y comprobaciones visibles para recorridos funcionales."""

import os
from pathlib import Path
from time import perf_counter


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
            not in ("click", "fill", "press", "select", "upload", "wait_visible")
        ):
            raise ValueError("Cada paso requiere ID único, acción y control declarado.")
        identifiers.add(identifier)
        value = action.get("value")
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
        prepared.append((identifier, kind, controls[control], value))
    if not any(
        kind in ("click", "press", "upload", "select") for _, kind, _, _ in prepared
    ):
        raise ValueError("El recorrido necesita una interacción que ejecute la tarea.")
    control_checks = {"control_visible", "control_text", "control_contains"}
    visible_checks = control_checks | {"visible_text"}
    if not any(check["type"] in visible_checks for check in checks.values()):
        raise ValueError("El recorrido necesita comprobar un resultado visible.")
    for check in checks.values():
        if check["type"] in control_checks and (
            not isinstance(check.get("control"), str)
            or check["control"] not in controls
        ):
            raise ValueError("La comprobación requiere un control declarado.")
    return prepared


def perform_steps(page, steps, checks, controls, responses, browser_error, expect):
    execution = []
    completed = True
    for identifier, kind, selector, value in steps:
        tick = perf_counter()
        locator = page.locator(selector)
        try:
            if kind == "click":
                locator.click(timeout=15000)
            elif kind == "wait_visible":
                locator.wait_for(state="visible", timeout=15000)
            elif kind == "fill":
                locator.fill(value, timeout=15000)
            elif kind == "press":
                locator.press(value, timeout=15000)
            elif kind == "select":
                locator.select_option(value, timeout=15000)
            else:
                locator.set_input_files(value, timeout=15000)
        except browser_error:
            completed = False
        execution.append(
            {
                "id": identifier,
                "type": kind,
                "outcome": "observed" if completed else "action_error",
                "duration_ms": round((perf_counter() - tick) * 1000),
            }
        )
        if not completed:
            break

    verified = {}
    for identifier, check in sorted(
        checks.items(), key=lambda item: item[1]["type"] == "network_status"
    ):
        if not completed:
            verified[identifier] = False
            continue
        kind = check["type"]
        expected = check.get("equals")
        if kind == "network_status":
            verified[identifier] = bool(responses) and responses[-1] == expected
            continue
        try:
            if kind == "visible_text":
                expect(page.get_by_text(expected, exact=True).first).to_be_visible(
                    timeout=15000
                )
            else:
                locator = page.locator(controls[check["control"]])
                expect(locator).to_be_visible(timeout=15000)
                if kind == "control_text":
                    expect(locator).to_have_text(expected, timeout=15000)
                elif kind == "control_contains":
                    expect(locator).to_contain_text(expected, timeout=15000)
        except (AssertionError, browser_error):
            verified[identifier] = False
        else:
            verified[identifier] = True
    return verified, execution
