"""Comprobar autenticación y capacidad de interacción una vez por actor y corrida."""

import os
from time import perf_counter

from browser_steps import BrowserDataUnavailable, prepare_steps


def validar_login(login, steps, profile):
    if (
        not isinstance(login, dict)
        or set(login) - {"step", "method", "path", "status"}
        or not isinstance(login.get("path"), str) or "?" in login["path"]
        or not any(
            action.get("id") == login.get("step") and action.get("type") == "click"
            for action in steps if isinstance(action, dict)
        )
        or not any(
            operation["method"] == login.get("method") and operation["path"] == login["path"]
            for operation in profile.get("http_operations", [])
        )
        or "status" in login and (
            type(login["status"]) is not int or not 100 <= login["status"] <= 599
        )
    ):
        raise ValueError("Login requiere un paso click y un método y ruta sin query declarados en el perfil.")


def criterio_listo(control):
    return {"id": "ui-ready", "expected": "Control disponible", "check": {"type": "control_visible", "control": control}}


def flujo_sesion(setup):
    probe = setup.get("probe") or {}
    return {
        "browser_flow": "web_ui",
        "browser_steps": [
            *setup["browser_steps"],
            {"id": "__preflight-ready", "type": "wait_visible", "control": setup["ready_control"]},
            *probe.get("browser_steps", []),
        ],
        "criteria": [criterio_listo(setup["ready_control"]), *probe.get("criteria", [])],
    }


def validar_setups(profile):
    from runners import checks_for

    setups = profile.get("browser_setups", {})
    controls = profile.get("browser_controls", {})
    if not isinstance(setups, dict):
        raise ValueError("browser_setups debe ser un objeto por sesión.")
    actors = set()
    for alias, setup in setups.items():
        if not alias.isidentifier() or not isinstance(setup, dict):
            raise ValueError("Cada sesión debe tener un alias identificador y una definición.")
        actor = setup.get("actor")
        ready = setup.get("ready_control")
        steps = setup.get("browser_steps")
        if (
            not isinstance(actor, str) or not actor.isidentifier() or actor in actors
            or setup.get("browser_path") not in profile.get("browser_paths", [])
            or not isinstance(ready, str) or ready not in controls
            or type(setup.get("timeout_seconds", 10)) is not int
            or not 1 <= setup.get("timeout_seconds", 10) <= 120
            or not isinstance(steps, list) or not steps
        ):
            raise ValueError("Cada sesión requiere actor único, ruta, pasos de login y control de disponibilidad.")
        actors.add(actor)
        validar_login(setup.get("login"), steps, profile)
        status = setup["login"].get("status")
        if status is not None and not 200 <= status < 300:
            raise ValueError("Una sesión compartida requiere login exitoso.")
        probe = setup.get("probe")
        if probe is not None and (
            not isinstance(probe, dict)
            or not isinstance(probe.get("browser_steps"), list) or not probe["browser_steps"]
            or not isinstance(probe.get("criteria"), list) or not probe["criteria"]
            or not any(
                isinstance(criterion, dict) and isinstance(criterion.get("check"), dict)
                and criterion["check"].get("type") in {"control_text", "control_contains"}
                for criterion in probe["criteria"]
            )
        ):
            raise ValueError("La prueba funcional opcional requiere pasos y al menos un criterio de texto específico.")
        all_steps = [*steps, *(probe["browser_steps"] if probe else [])]
        if any(not isinstance(step, dict) or step.get("type") in {"upload", "download"} for step in all_steps):
            raise ValueError("La preparación compartida requiere pasos sin fixtures ni descargas.")
        flow = flujo_sesion(setup)
        checks = checks_for(flow, "playwright")
        if any(check["type"] in {"network_status", "visible_text"} for check in checks.values()):
            raise ValueError("El preflight comprueba la respuesta del login y criterios sobre controles específicos.")
        placeholders = {step["value_env"]: "dato-de-validacion" for step in all_steps if isinstance(step.get("value_env"), str)}
        prepare_steps(flow, profile, None, checks, environment=placeholders)


def validar_caso_navegador(case, profile, channel):
    fields = {"browser_setup", "browser_session", "browser_login", "browser_preconditions", "browser_model"}
    if not fields.intersection(case):
        return
    if channel != "playwright" or case.get("browser_flow") != "web_ui":
        raise ValueError("Sesión, login y precondiciones requieren browser_flow web_ui.")
    steps = case.get("browser_steps", [])
    if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
        raise ValueError("El caso necesita browser_steps con pasos definidos.")
    if "browser_session" in case and case["browser_session"] != "fresh":
        raise ValueError("browser_session admite el valor fresh para una sesión aislada.")
    alias = case.get("browser_setup")
    if "browser_setup" in case and (
        not isinstance(alias, str) or alias not in profile.get("browser_setups", {})
        or "browser_login" in case or case.get("browser_session") == "fresh"
    ):
        raise ValueError("La sesión compartida debe existir en el perfil y no se combina con login aislado.")
    if "browser_login" in case:
        validar_login(case["browser_login"], steps, profile)
    guard = case.get("browser_preconditions", [])
    if not isinstance(guard, list) or any(
        not isinstance(condition, dict)
        or not isinstance(condition.get("control"), str)
        or condition["control"] not in profile.get("browser_controls", {})
        or not isinstance(condition.get("equals"), str) or not condition["equals"].strip()
        for condition in guard
    ):
        raise ValueError("Cada precondición requiere control del perfil y texto visible exacto.")
    if "browser_model" in case:
        model = case["browser_model"]
        if not isinstance(model, dict) or not all(
            isinstance(model.get(key), str) and model[key].strip() for key in ("value", "before")
        ):
            raise ValueError("browser_model requiere value y el ID before de la primera interacción con el modelo.")
        verificado = False
        for step in steps:
            if step.get("id") == model["before"] and verificado and step.get("type") in {"click", "press", "fill"}:
                break
            if step.get("type") == "verify_model" and step.get("value") == model["value"]:
                verificado = True
        else:
            raise ValueError("Verificá el modelo exacto antes del paso declarado en browser_model.before.")


def preparar_sesiones(cases, manifest, profile, run, blocked, *, environment=None):
    from runners import Unavailable, browser_request, checks_for

    environment = os.environ if environment is None else environment
    by_alias = {}
    for case in cases:
        if alias := case.get("browser_setup"):
            by_alias.setdefault(alias, []).append(case["id"])
    states, results = {}, {}

    def propagar():
        for item in manifest:
            if deps := [dep for dep in item.get("depends_on", []) if dep in blocked]:
                blocked.setdefault(item["case"], "Dependencias de preflight bloqueadas · " + ", ".join(deps))

    propagar()
    for alias, case_ids in by_alias.items():
        setup = profile["browser_setups"][alias]
        tick = perf_counter()
        row = {"actor": setup["actor"], "casos": case_ids, "estado": "omitido"}
        if any(key not in blocked for key in case_ids):
            flow = flujo_sesion(setup)
            try:
                checks = checks_for(flow, "playwright")
                steps = prepare_steps(flow, profile, run, checks, environment=environment)
                secrets = tuple(environment.get(step["value_env"]) for step in flow["browser_steps"] if "value_env" in step)
                verdicts, result = browser_request(
                    {**profile, "timeout_seconds": setup.get("timeout_seconds", 10)},
                    setup["browser_path"], checks, workflow=("web_ui", None, steps, secrets),
                    capture_state=True, login=setup["login"],
                )
                row["pasos"] = result.get("browser_steps", [])
                row["login"] = next((s["login"] for s in row["pasos"] if "login" in s), None)
                row["criterios"] = verdicts
                if verdicts and all(verdicts.values()):
                    states[alias] = result["storage_state"]
                    row["estado"] = "listo"
                else:
                    cause = result.get("cause", "prueba_funcional_no_comprobada")
                    if any(s["id"] == "__preflight-ready" and s["outcome"] == "action_error" for s in row["pasos"]):
                        cause = "control_de_disponibilidad_ausente"
                    row.update(estado="bloqueado", causa=cause)
            except (Unavailable, OSError):
                row.update(estado="bloqueado", causa="navegacion_o_navegador_no_disponible")
            except BrowserDataUnavailable:
                row.update(estado="bloqueado", causa="credenciales_ausentes")
            except ValueError:
                row.update(estado="bloqueado", causa="contrato_del_preflight_invalido")
            if row["estado"] == "bloqueado":
                for key in case_ids:
                    blocked.setdefault(key, f"Sesión {alias} · {row['causa']}.")
                propagar()
        row["duracion_ms"] = round((perf_counter() - tick) * 1000)
        results[alias] = row
    return states, results
