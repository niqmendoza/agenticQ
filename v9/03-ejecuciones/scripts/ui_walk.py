"""Recorridos funcionales reproducibles en una sola sesión de navegador."""

from random import Random
from time import perf_counter


def walk_plan(config, profile):
    if not isinstance(config, dict):
        raise ValueError("browser_walk debe ser un objeto.")
    seed, rounds = config.get("seed"), config.get("rounds", 1)
    actions = config.get("actions")
    if type(seed) is not int or type(rounds) is not int or not 1 <= rounds <= 3:
        raise ValueError("El recorrido requiere seed entero y entre una y tres rondas.")
    if not isinstance(actions, list) or not 2 <= len(actions) <= 8:
        raise ValueError("El recorrido requiere entre dos y ocho acciones.")
    identifiers = set()
    for action in actions:
        if not isinstance(action, dict):
            raise ValueError("Cada acción del recorrido debe ser un objeto.")
        name, kind = action.get("id"), action.get("type")
        if not isinstance(name, str) or not name.strip() or name in identifiers:
            raise ValueError("Cada acción necesita un ID único.")
        identifiers.add(name)
        if kind in ("click", "double_click"):
            control = action.get("control")
            if not isinstance(control, str) or control not in profile.get(
                "browser_controls", {}
            ):
                raise ValueError("El control debe estar declarado en browser_controls.")
        elif kind == "resize":
            if not all(
                type(action.get(key)) is int and lower <= action[key] <= upper
                for key, lower, upper in (("width", 320, 1920), ("height", 480, 1200))
            ):
                raise ValueError(
                    "Dimensiones de ventana fuera de los límites del recorrido."
                )
        elif kind == "scroll":
            distance = action.get("pixels")
            if (
                type(distance) is not int
                or not -1800 <= distance <= 1800
                or distance == 0
            ):
                raise ValueError(
                    "scroll requiere una distancia no nula de hasta 1800 píxeles."
                )
        elif kind != "reload":
            raise ValueError("Acción no soportada por el recorrido.")
    random = Random(seed)
    sequence = []
    for _ in range(rounds):
        batch = list(actions)
        random.shuffle(batch)
        sequence.extend(batch)
    return sequence


def inspect_page(page, status, checks, timeout_error):
    verdicts = {}
    for identifier, check in checks.items():
        if check["type"] == "status":
            verdicts[identifier] = status == check["equals"]
        elif check["type"] == "visible_text":
            try:
                page.get_by_text(check["equals"], exact=True).first.wait_for(
                    state="visible", timeout=5000
                )
            except timeout_error:
                verdicts[identifier] = False
            else:
                verdicts[identifier] = True
    return verdicts


def perform_action(page, action, controls, status):
    kind = action["type"]
    if kind == "resize":
        page.set_viewport_size({"width": action["width"], "height": action["height"]})
    elif kind == "scroll":
        page.mouse.wheel(0, action["pixels"])
    elif kind == "reload":
        response = page.reload(wait_until="domcontentloaded", timeout=15000)
        return response.status if response else None
    else:
        locator = page.locator(controls[action["control"]])
        if kind == "double_click":
            locator.dblclick(timeout=5000)
        else:
            locator.click(timeout=5000)
    return status


def run_walk(
    page,
    profile,
    path,
    status,
    checks,
    config,
    plan,
    errors,
    browser_error,
    timeout_error,
):
    expected_url = profile["base_url"].rstrip("/") + path
    baseline = inspect_page(page, status, checks, timeout_error)
    verdicts = dict(baseline)
    steps = []
    # Una navegación por hash de Swagger conserva la misma página.
    in_scope = page.url.split("#", 1)[0] == expected_url
    completed = in_scope and all(baseline.values())
    if completed:
        for action in plan:
            started = perf_counter()
            step = {
                key: action[key]
                for key in ("id", "type", "width", "height", "pixels", "control")
                if key in action
            }
            try:
                status = perform_action(
                    page, action, profile.get("browser_controls", {}), status
                )
            except browser_error:
                step["outcome"] = "action_error"
                completed = False
            else:
                if page.url.split("#", 1)[0] != expected_url:
                    step["outcome"] = "unexpected_navigation"
                    completed = False
                else:
                    observed = inspect_page(page, status, checks, timeout_error)
                    step.update(outcome="observed", checks=observed, http_status=status)
                    for key, passed in observed.items():
                        verdicts[key] &= passed
            step["duration_ms"] = round((perf_counter() - started) * 1000)
            steps.append(step)
            if not completed:
                break

    for identifier, check in checks.items():
        if check["type"] == "walk_completed":
            verdicts[identifier] = completed and len(steps) == len(plan)
        elif check["type"] == "no_page_errors":
            verdicts[identifier] = completed and not errors
    return verdicts, {
        "http_status": status,
        "seed": config["seed"],
        "planned_order": [action["id"] for action in plan],
        "baseline": baseline,
        "steps": steps,
        "page_error_count": len(errors),
    }
