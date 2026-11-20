"""Ejecutores funcionales HTTP y Playwright. Solo guardan resultados de aserciones."""

import json
import os
from contextlib import contextmanager
from http.client import HTTPException
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4

from bindings import SAFE_ID, bind, bind_profile
from browser_steps import BrowserDataUnavailable, perform_steps, prepare_steps
from contracts import criteria_by_id, derive_status
from database_runner import (
    DatabaseUnavailable,
    query_arguments,
    read_rows,
    validate_database,
)
from json_tools import JSON_TYPES, json_at, valid_path
from markdown import inline, table, write_markdown
from records import store_records
from session import (
    load,
    timestamp,
)
from token_meter import require_usage_ready
from ui_walk import inspect_page, run_walk, walk_plan

HTTP_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
MAX_BODY = 2 * 1024 * 1024


class Unavailable(Exception):
    def __init__(self, message, classification="environment"):
        super().__init__(message)
        self.classification = classification


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def origin(url):
    parts = urlsplit(url)
    return (
        parts.scheme,
        parts.hostname,
        parts.port or (443 if parts.scheme == "https" else 80),
    )


def target_path(path):
    if (
        not isinstance(path, str)
        or not path.startswith("/")
        or path.startswith("//")
        or any(char in path for char in ("#", "\\", "\r", "\n", "\t", " "))
    ):
        raise ValueError("Usá una ruta HTTP relativa al origen, con / inicial.")
    return path


def profile_for_run(profile, *, chrome_visible=False):
    validate_profile(profile)
    if chrome_visible:
        return {**profile, "browser_channel": "chrome", "browser_headless": False}
    return profile


def validate_profile(profile):
    if not isinstance(profile, dict):
        raise ValueError("El perfil debe ser un objeto.")
    base_url = profile.get("base_url")
    if base_url is None:
        if any(profile.get(key) for key in ("http_operations", "browser_paths")):
            raise ValueError("HTTP y navegador requieren base_url.")
    else:
        validate_origin(base_url)
    if "browser_channel" in profile and profile["browser_channel"] not in (
        "chrome",
        "msedge",
        "chromium",
    ):
        raise ValueError("browser_channel debe ser chrome, msedge o chromium.")
    if type(profile.get("browser_headless", True)) is not bool:
        raise ValueError("browser_headless debe ser true o false.")
    for key in ("http_operations", "browser_paths", "db_sources"):
        if not isinstance(profile.get(key, []), list):
            raise ValueError(f"{key} debe ser una lista.")
    credentials = profile.get("credentials", {})
    if not isinstance(credentials, dict) or not all(
        actor.isidentifier()
        and actor != "anonymous"
        and isinstance(env, str)
        and env.isidentifier()
        for actor, env in credentials.items()
    ):
        raise ValueError(
            "credentials debe asociar cada actor con el nombre de su variable de entorno."
        )
    allowed_actors = {"anonymous", *credentials}
    operations = set()
    for operation in profile.get("http_operations", []):
        if (
            not isinstance(operation, dict)
            or operation.get("method") not in HTTP_METHODS
        ):
            raise ValueError("Cada operación HTTP necesita un método válido.")
        path = target_path(operation.get("path"))
        key = (operation["method"], path)
        if key in operations:
            raise ValueError("El perfil contiene una operación HTTP duplicada.")
        operations.add(key)
        actors = operation.get("actors", ["anonymous"])
        if (
            not isinstance(actors, list)
            or not actors
            or not all(
                isinstance(actor, str) and actor in allowed_actors for actor in actors
            )
        ):
            raise ValueError("Cada operación debe indicar actores válidos del perfil.")
        if "probe" in operation:
            probe = operation["probe"]
            if (
                operation["method"] not in ("GET", "HEAD")
                or not isinstance(probe, dict)
                or probe.get("actor", "anonymous") not in actors
                or type(probe.get("status", 200)) is not int
                or not 100 <= probe.get("status", 200) <= 599
                or "content_type" in probe
                and not isinstance(probe["content_type"], str)
            ):
                raise ValueError(
                    "Una sonda requiere GET/HEAD, actor autorizado y respuesta esperada válida."
                )
    timeout = profile.get("timeout_seconds", 15)
    if type(timeout) is not int or not 1 <= timeout <= 120:
        raise ValueError("timeout_seconds debe ser un entero entre 1 y 120.")
    validate_browser_and_db(profile)
    if "database" in profile:
        validate_database(profile["database"])


def validate_origin(base_url):
    if not isinstance(base_url, str):
        raise ValueError("base_url debe ser un origen HTTP(S).")
    parts = urlsplit(base_url)
    if (
        parts.scheme not in ("http", "https")
        or not parts.hostname
        or parts.username is not None
        or (parts.path not in ("", "/") or parts.query or parts.fragment)
    ):
        raise ValueError(
            "base_url debe ser un origen HTTP(S) sin ruta ni credenciales."
        )
    origin(base_url)


def validate_browser_and_db(profile):
    for path in profile.get("browser_paths", []):
        target_path(path)
    controls = profile.get("browser_controls", {})
    if not isinstance(controls, dict) or not all(
        isinstance(name, str)
        and name.strip()
        and isinstance(selector, str)
        and selector.strip()
        for name, selector in controls.items()
    ):
        raise ValueError(
            "browser_controls debe asociar nombres de controles con selectores."
        )
    assets = profile.get("browser_assets", [])
    if not isinstance(assets, list) or not all(isinstance(url, str) for url in assets):
        raise ValueError("browser_assets debe contener URLs HTTPS exactas.")
    for url in assets:
        asset = urlsplit(url)
        if (
            asset.scheme != "https"
            or not asset.hostname
            or asset.username is not None
            or asset.query
            or asset.fragment
        ):
            raise ValueError(
                "Cada recurso de navegador necesita una URL HTTPS exacta sin credenciales ni query."
            )
    if not all(
        isinstance(source, str) and source.strip()
        for source in profile.get("db_sources", [])
    ):
        raise ValueError(
            "db_sources debe contener identificadores de herramientas MCP."
        )


def checks_for(case, method):
    checks = {}
    for identifier, criterion in criteria_by_id(case["criteria"]).items():
        check = criterion.get("check")
        if not isinstance(check, dict):
            raise ValueError(f"Falta check ejecutable para {identifier}.")
        kind, expected = check.get("type"), check.get("equals")
        if case.get("browser_flow") and method == "playwright":
            valid = (
                kind == "control_visible"
                and isinstance(check.get("control"), str)
                and bool(check["control"].strip())
                and "equals" not in check
                or kind in ("visible_text", "control_text", "control_contains")
                and isinstance(expected, str)
                and bool(expected)
                or kind == "network_status"
                and type(expected) is int
                and 100 <= expected <= 599
            )
            if not valid:
                raise ValueError(
                    f"Comprobación interactiva inválida para {identifier}."
                )
            checks[identifier] = check
            continue
        valid = (
            kind == "status"
            and method in ("http", "playwright")
            and type(expected) is int
            and 100 <= expected <= 599
            or method == "http"
            and kind == "response_schema"
            and isinstance(check.get("schema"), (dict, bool))
            and type(check.get("status")) is int
            or method == "http"
            and kind == "content_type"
            and isinstance(expected, str)
            and bool(expected)
            or method in ("http", "db")
            and kind in ("json_equals", "json_type")
            and "equals" in check
            and valid_path(check.get("path"))
            and (
                kind == "json_equals"
                or isinstance(expected, str)
                and expected in JSON_TYPES
            )
            or method == "db"
            and kind == "row_count"
            and type(expected) is int
            and 0 <= expected <= 100
            or method == "playwright"
            and kind in ("walk_completed", "no_page_errors")
            and "browser_walk" in case
            or method == "playwright"
            and kind == "visible_text"
            and isinstance(expected, str)
            and bool(expected)
        )
        if not valid:
            raise ValueError(f"Aserción inválida para {identifier}.")
        checks[identifier] = check
    return checks


def request_headers(profile, fixture, actor):
    headers = {"Accept": "application/json"}
    if fixture is not None:
        headers["Content-Type"] = "application/json"
    if actor != "anonymous":
        token = os.environ.get(profile["credentials"][actor])
        if not token:
            raise Unavailable("Falta la credencial configurada para el caso.")
        headers["Authorization"] = "Bearer " + token
    return headers


def http_request(profile, operation, checks, fixture, actor):
    method, path = operation["method"], operation["path"]
    headers = request_headers(profile, fixture, actor)
    request = Request(
        profile["base_url"].rstrip("/") + path,
        data=fixture,
        method=method,
        headers=headers,
    )
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        response = opener.open(request, timeout=profile.get("timeout_seconds", 15))
    except HTTPError as error:
        response = error
    with response:
        status = response.code
        media_type = (
            response.headers.get_content_type()
            if "Content-Type" in response.headers
            else None
        )
        body = (
            response.read(MAX_BODY + 1)
            if any(
                c["type"] in ("json_equals", "json_type", "response_schema")
                for c in checks.values()
            )
            else b""
        )
    return evaluate_response(status, media_type, body, checks)


def evaluate_response(status, media_type, body, checks):
    if len(body) > MAX_BODY and any(
        c["type"] in {"json_equals", "json_type", "response_schema"}
        for c in checks.values()
    ):
        raise Unavailable("El documento supera el límite de validación.", "runner")
    data = None
    parsed = False
    if (
        len(body) <= MAX_BODY
        and media_type
        and (media_type == "application/json" or media_type.endswith("+json"))
    ):
        try:
            data = json.loads(body)
            parsed = True
        except (ValueError, UnicodeError):
            pass
    results = {}
    observations = {}
    for identifier, check in checks.items():
        kind = check["type"]
        if kind == "status":
            observations[identifier] = f"HTTP {status}."
            results[identifier] = status == check["equals"]
        elif kind == "content_type":
            observations[identifier] = f"Tipo de contenido observado: {media_type}."
            results[identifier] = media_type == check["equals"]
        elif kind == "response_schema":
            from openapi_contract import schema_validator

            validator = schema_validator(check["schema"])
            error = next(validator.iter_errors(data), None) if parsed else None
            results[identifier] = (
                parsed
                and error is None
                and status == check["status"]
                and media_type == check.get("media_type", "application/json")
            )
            observations[identifier] = f"HTTP {status} · {media_type} · " + (
                f"regla incumplida {error.validator}"
                if error
                else ("JSON válido" if parsed else "JSON no evaluable")
            )
        else:
            results[identifier] = json_result(data, check)
            observations[identifier] = json_observation(data, check)
    return results, {
        "http_status": status,
        "content_type": media_type,
        "observations": observations,
    }


def json_observation(data, check):
    field = ".".join(map(str, check["path"]))
    try:
        value = json_at(data, check["path"])
    except (KeyError, IndexError):
        return f"Campo {field} ausente o documento ilegible."
    allowed = check.get("report_values", [])
    if type(value) in (bool, type(None)) or value in allowed:
        return f"Campo {field} · {json.dumps(value, ensure_ascii=False)}"
    return f"Campo {field} presente · tipo {type(value).__name__}. Valor reservado."


def api_request(profile, operation, checks, fixture, actor, capture=None):
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        raise Unavailable("Falta instalar Playwright para API.", "runner") from None
    headers = request_headers(profile, fixture, actor)
    try:
        with sync_playwright() as playwright:
            context = playwright.request.new_context(extra_http_headers=headers)
            try:
                response = context.fetch(
                    profile["base_url"].rstrip("/") + operation["path"],
                    method=operation["method"],
                    data=fixture,
                    max_redirects=0,
                    timeout=1000 * profile.get("timeout_seconds", 15),
                )
                media = (
                    response.headers.get("content-type", "")
                    .partition(";")[0]
                    .strip()
                    .lower()
                )
                body = response.body()
                results, metadata = evaluate_response(
                    response.status, media, body, checks
                )
                if capture and all(results.values()):
                    values = {}
                    for name, path in capture.items():
                        try:
                            raw = json_at(json.loads(body), path)
                        except (ValueError, KeyError, IndexError):
                            raise Unavailable(
                                "La respuesta no contiene el ID sintético declarado."
                            ) from None
                        if type(raw) not in (int, str) or not SAFE_ID.fullmatch(
                            str(raw)
                        ):
                            raise Unavailable(
                                "El valor capturado requiere un identificador de fixture válido."
                            )
                        values[name] = str(raw)
                    metadata["bindings"] = values
                return results, metadata
            finally:
                context.dispose()
    except Error:
        raise Unavailable("El cliente API no pudo completar la solicitud.") from None


def json_result(data, check):
    try:
        value = json_at(data, check["path"])
    except (KeyError, IndexError):
        return False
    expected = check["equals"]
    if check["type"] == "json_type":
        return type(value) in JSON_TYPES[expected]
    return type(value) is type(expected) and value == expected


def database_request(profile, case, checks):
    database, query, values = query_arguments(profile, case)
    rows = read_rows(database, query, values)
    data = [dict(zip(query["columns"], row)) for row in rows[:100]]
    verdicts = {
        identifier: len(rows) == check["equals"]
        if check["type"] == "row_count"
        else json_result(data, check)
        for identifier, check in checks.items()
    }
    observations = {
        key: (
            f"Filas observadas · {len(data)}"
            if check["type"] == "row_count"
            else json_observation(data, check)
        )
        for key, check in checks.items()
    }
    return verdicts, {
        "rows_observed": len(data),
        "rows_truncated": len(rows) > 100,
        "observations": observations,
    }


def browser_description(profile):
    channel = profile.get("browser_channel", "Chromium administrado")
    mode = "sin ventana" if profile.get("browser_headless", True) else "ventana visible"
    return f"{channel} · {mode}"


@contextmanager
def playwright_browser(profile):
    try:
        from playwright.sync_api import (
            Error,
            sync_playwright,
        )
        from playwright.sync_api import (
            TimeoutError as PlaywrightTimeout,
        )
    except ImportError:
        raise Unavailable(
            "Playwright para Python no está instalado.", "runner"
        ) from None
    with sync_playwright() as playwright:
        try:
            options = (
                {"channel": profile["browser_channel"]}
                if "browser_channel" in profile
                else {}
            )
            browser = playwright.chromium.launch(
                headless=profile.get("browser_headless", True), **options
            )
        except Error:
            raise Unavailable(
                f"No se pudo iniciar el navegador solicitado ({browser_description(profile)}).",
                "runner",
            ) from None
        try:
            yield browser, Error, PlaywrightTimeout
        finally:
            browser.close()


def browser_request(profile, path, checks, config=None, plan=None, workflow=None):
    target = origin(profile["base_url"])
    with playwright_browser(profile) as (browser, Error, PlaywrightTimeout):
        page = browser.new_page(service_workers="block")
        errors = []
        responses = []
        blocked_requests = []
        if workflow is not None:
            flow_kind, operation, steps = workflow

            def observe_response(response):
                request = response.request
                if (
                    operation
                    and origin(request.url) == target
                    and request.method == operation["method"]
                    and browser_url_path(request.url) == operation["path"]
                ):
                    responses.append(response.status)

            page.on("response", observe_response)
        if config is not None:
            page.on("pageerror", lambda _: errors.append(True))

        def route_request(route):
            request = route.request
            same_origin = origin(request.url) == target
            if (
                workflow is not None
                and request.is_navigation_request()
                and (
                    not same_origin
                    or browser_url_path(request.url)
                    not in profile.get("browser_paths", [])
                )
            ):
                route.abort()
                return
            if config is not None and request.is_navigation_request():
                location = urlsplit(request.url)
                expected = urlsplit(path)
                if not same_origin or (location.path, location.query) != (
                    expected.path,
                    expected.query,
                ):
                    route.abort()
                    return
            approved_asset = request.url in profile.get(
                "browser_assets", []
            ) and request.resource_type in ("script", "stylesheet")
            allowed_mutation = (
                workflow is not None
                and same_origin
                and any(
                    operation["method"] == request.method
                    and operation["path"] == browser_url_path(request.url)
                    for operation in profile.get("http_operations", [])
                )
            )
            if (
                allowed_mutation
                or request.method in ("GET", "HEAD")
                and (same_origin or approved_asset)
            ):
                # Playwright puede continuar una redirección sin volver a llamar al handler.
                try:
                    headers = (
                        None
                        if same_origin
                        else {
                            key: value
                            for key, value in request.headers.items()
                            if key.lower() in ("accept", "user-agent")
                        }
                    )
                    fetched = route.fetch(
                        headers=headers,
                        max_redirects=0,
                        timeout=60000 if workflow else 15000,
                    )
                except Error:
                    route.abort()
                    return
                if 300 <= fetched.status < 400:
                    if workflow is not None and (
                        request.is_navigation_request() or allowed_mutation
                    ):
                        blocked_requests.append(
                            "La navegación u operación redirigió a otra ruta."
                        )
                    route.abort()
                else:
                    route.fulfill(response=fetched)
            else:
                if (
                    workflow is not None
                    and same_origin
                    and request.method not in ("GET", "HEAD")
                ):
                    blocked_requests.append(
                        "El recorrido intentó una operación no declarada en el perfil."
                    )
                route.abort()

        page.context.route("**/*", route_request)
        try:
            response = page.goto(
                profile["base_url"].rstrip("/") + path,
                wait_until="domcontentloaded",
                timeout=15000,
            )
        except Error:
            raise Unavailable(
                "Playwright no pudo cargar la página del perfil."
            ) from None
        status = response.status if response else None
        if workflow is not None:
            from playwright.sync_api import expect

            if flow_kind == "swagger_ui" and (status is None or status >= 400):
                raise Unavailable("Swagger UI no está disponible en la ruta declarada.")
            verified, actions = perform_steps(
                page,
                steps,
                checks,
                profile.get("browser_controls", {}),
                responses,
                Error,
                expect,
            )
            metadata = {
                "http_status": status,
                "browser_steps": actions,
                "operation_statuses": responses,
            }
            failed_step = next(
                (step for step in actions if step["outcome"] == "action_error"), None
            )
            if failed_step:
                return None, {
                    **metadata,
                    "blocked_reason": f"Paso {failed_step['id']} incompleto. Los criterios posteriores quedaron sin observar.",
                }
            if flow_kind == "swagger_ui" and not responses:
                reason = (
                    blocked_requests[0]
                    if blocked_requests
                    else "Playwright no observó la ejecución de la operación desde Swagger."
                )
                return None, {**metadata, "blocked_reason": reason}
            if blocked_requests and not all(verified.values()):
                return None, {**metadata, "blocked_reason": blocked_requests[0]}
            return verified, metadata
        if config is not None:
            return run_walk(
                page,
                profile,
                path,
                status,
                checks,
                config,
                plan,
                errors,
                Error,
                PlaywrightTimeout,
            )
        return inspect_page(page, status, checks, PlaywrightTimeout), {
            "http_status": status
        }


def browser_url_path(url):
    parts = urlsplit(url)
    return parts.path + (f"?{parts.query}" if parts.query else "")


def browser_operation(case, profile, checks):
    operation = case.get("browser_operation")
    needs_response = any(check["type"] == "network_status" for check in checks.values())
    if case["browser_flow"] == "swagger_ui" and not needs_response:
        raise ValueError(
            "Swagger requiere observar el estado de la operación ejecutada en el navegador."
        )
    if operation is None and not needs_response:
        return None
    if not isinstance(operation, dict) or not any(
        allowed["method"] == operation.get("method")
        and allowed["path"] == operation.get("path")
        for allowed in profile.get("http_operations", [])
    ):
        raise ValueError(
            "La operación observada debe estar autorizada en http_operations."
        )
    return operation


def run_case(args):
    run, meta, events = load(args.run)
    require_usage_ready(run, meta)
    plan_file = run / "plan.json"
    if not plan_file.is_file():
        raise ValueError("Congelá el plan antes de ejecutar un caso.")
    profile = meta["profile"]
    case = next(
        (
            event
            for event in events
            if event["kind"] == "case" and event["id"] == args.case
        ),
        None,
    )
    if not case:
        raise ValueError("Caso no registrado.")
    variables = getattr(args, "bindings", None)
    if variables is not None:
        case = bind(case, variables)
        profile = bind_profile(profile, variables)
    method = args.via
    browser_flow = case.get("browser_flow")
    if browser_flow and method != "playwright":
        raise ValueError("El recorrido interactivo requiere Playwright.")
    checks = checks_for(case, "http" if method == "api" else method)
    fixture = None
    config = case.get("browser_walk")
    seed = getattr(args, "seed", None)
    if seed is not None:
        if not isinstance(config, dict):
            raise ValueError("--seed requiere un caso con browser_walk.")
        config = {**config, "seed": seed}
    plan = None
    if "browser_walk" in case:
        if method != "playwright" or not any(
            check["type"] == "walk_completed" for check in checks.values()
        ):
            raise ValueError(
                "El recorrido requiere Playwright y un criterio walk_completed."
            )
        plan = walk_plan(config, profile)
    if method in ("http", "api"):
        op = case.get("http")
        if not isinstance(op, dict) or not isinstance(
            op.get("actor", "anonymous"), str
        ):
            raise ValueError(
                "El caso HTTP requiere método, ruta y, opcionalmente, actor."
            )
        path = target_path(op.get("path"))
        actor = op.get("actor", "anonymous")
        operation = next(
            (
                item
                for item in profile.get("http_operations", [])
                if item["method"] == op.get("method") and item["path"] == path
            ),
            None,
        )
        if operation is None or actor not in operation.get("actors", ["anonymous"]):
            raise ValueError("Método, ruta o actor fuera del perfil de ejecución.")
        if args.body:
            if op["method"] in ("GET", "HEAD"):
                raise ValueError("El caso GET/HEAD no admite --body.")
            with Path(args.body).open("rb") as body_file:
                fixture = body_file.read(MAX_BODY + 1)
            if len(fixture) > MAX_BODY:
                raise ValueError("El fixture JSON supera el límite.")
            payload = json.loads(fixture)
            if variables is not None:
                fixture = json.dumps(
                    bind(payload, variables), ensure_ascii=False
                ).encode()
    elif method == "db":
        if args.body:
            raise ValueError("Usá db.parameters para los valores de consulta.")
    else:
        path = target_path(case.get("browser_path"))
        if path not in profile.get("browser_paths", []) or args.body:
            raise ValueError(
                "Ruta de navegador fuera del perfil o --body incompatible."
            )
    if case["oracle_status"] == "pending":
        raise ValueError("Resolver el oráculo antes de ejecutar el caso.")

    started, tick = timestamp(), perf_counter()
    evidence_path = f"evidencias/{args.case}-{uuid4().hex}.md"
    blocked_class = None
    workflow = None
    try:
        if browser_flow:
            workflow = (
                browser_flow,
                browser_operation(case, profile, checks),
                prepare_steps(case, profile, run, checks),
            )
        if method == "db":
            verdicts, metadata = database_request(profile, case, checks)
        elif method == "api":
            verdicts, metadata = api_request(
                profile,
                operation,
                checks,
                fixture,
                actor,
                getattr(args, "capture", None),
            )
        elif method == "http":
            verdicts, metadata = http_request(
                profile, operation, checks, fixture, actor
            )
        else:
            verdicts, metadata = browser_request(
                profile, path, checks, config, plan, workflow
            )
            metadata["browser"] = browser_description(profile)
    except (BrowserDataUnavailable, DatabaseUnavailable) as error:
        blocked_class = "environment"
        verdicts, metadata = None, {"blocked_reason": str(error)}
    except Unavailable as error:
        blocked_class = error.classification
        verdicts, metadata = None, {"blocked_reason": str(error)}
    except (OSError, HTTPException):
        blocked_class = "inconclusive"
        verdicts, metadata = (
            None,
            {"blocked_reason": "La conexión o lectura del entorno no se completó."},
        )
    if verdicts is None and blocked_class is None:
        blocked_class = "inconclusive"
    finished = timestamp()
    duration = round((perf_counter() - tick) * 1000)
    results = [
        {
            "id": identifier,
            "status": (
                ("passed" if verdicts[identifier] else "failed")
                if verdicts is not None
                else "blocked"
            ),
            "observation": (
                (
                    metadata.get("observations", {}).get(identifier)
                    or (
                        "Coincide con lo esperado."
                        if verdicts[identifier]
                        else "Difiere de lo esperado."
                    )
                )
                if verdicts is not None
                else metadata["blocked_reason"]
            ),
            "evidence": evidence_path,
        }
        for identifier in checks
    ]
    status = derive_status(results)
    observation = metadata.get("blocked_reason")
    if observation is None:
        statuses = metadata.get("operation_statuses", [])
        status_code = statuses[-1] if statuses else metadata.get("http_status")
        count = sum(result["status"] == "passed" for result in results)
        observation = (
            f"{count} de {len(results)} comprobaciones coincidieron con lo esperado."
        )
        if status_code is not None:
            observation = f"HTTP {status_code}. {observation}"
    write_markdown(
        run / evidence_path,
        execution_evidence(case, method, status, results, metadata, duration),
    )
    store_records(
        run,
        meta,
        events,
        {
            "kind": "execution",
            "case_id": args.case,
            "status": status,
            "observation": observation,
            "evidence": evidence_path,
            "execution_method": method,
            "executor": "runner",
            **({"classification": blocked_class} if blocked_class else {}),
            "results": results,
            "started_at": started,
            "finished_at": finished,
            "duration_ms": duration,
        },
    )
    if variables is not None and status == "passed":
        variables.update(metadata.get("bindings", {}))
    print(run / evidence_path)
    return {"passed": 0, "failed": 1, "blocked": 3}[status]


def execution_evidence(case, method, status, results, metadata, duration):
    lines = [
        f"# Evidencia · {inline(case['id'])}",
        "",
        f"- Escenario · {inline(case['scenario'])}",
        f"- Método y resultado · {method} / {status}",
        f"- Duración en ms · {duration}",
    ]
    if "browser" in metadata:
        lines.append(f"- Navegador · {inline(metadata['browser'])}")
    if "blocked_reason" in metadata:
        lines.append(f"- Bloqueo · {inline(metadata['blocked_reason'])}")
    elif "http_status" in metadata:
        lines.append(f"- Estado HTTP observado · {inline(metadata.get('http_status'))}")
    if "rows_observed" in metadata:
        suffix = " o más" if metadata["rows_truncated"] else ""
        lines.append(f"- Filas observadas · {metadata['rows_observed']}{suffix}")
    if "content_type" in metadata:
        lines.append(f"- Tipo de contenido · {inline(metadata['content_type'])}")
    if "seed" in metadata:
        lines += [
            f"- Semilla · {inline(metadata['seed'])}",
            f"- Orden de acciones · {inline(', '.join(metadata['planned_order']))}",
            f"- Excepciones de página · {inline(metadata['page_error_count'])}",
            "",
            *table(
                ("Acción", "Resultado", "Estado HTTP", "Duración en ms"),
                (
                    (
                        inline(step["id"]),
                        inline(step["outcome"]),
                        inline(step.get("http_status")),
                        step["duration_ms"],
                    )
                    for step in metadata["steps"]
                ),
            ),
        ]
    if "browser_steps" in metadata:
        lines += [
            "",
            *table(
                ("Paso", "Interacción", "Resultado", "Duración en ms"),
                (
                    (
                        inline(step["id"]),
                        step["type"],
                        step["outcome"],
                        step["duration_ms"],
                    )
                    for step in metadata["browser_steps"]
                ),
            ),
        ]
        statuses = metadata["operation_statuses"]
        if statuses:
            lines.append(
                f"- HTTP de la operación observada en el navegador · {', '.join(map(str, statuses))}"
            )
    expected = {
        criterion["id"]: criterion["expected"] for criterion in case["criteria"]
    }
    lines += [
        "",
        *table(
            ("Criterio", "Esperado", "Estado", "Observación"),
            (
                (
                    inline(row["id"]),
                    inline(expected[row["id"]]),
                    row["status"],
                    inline(row["observation"]),
                )
                for row in results
            ),
        ),
    ]
    return lines


def inventory(args):
    from openapi_contract import read_spec

    spec = read_spec(args.spec)
    if (
        not isinstance(spec, dict)
        or not ("openapi" in spec or "swagger" in spec)
        or not isinstance(spec.get("paths"), dict)
    ):
        raise ValueError("Se requiere una especificación OpenAPI/Swagger en JSON.")
    operations = []
    for path, methods in sorted(spec["paths"].items()):
        if isinstance(methods, dict):
            for method in HTTP_METHODS:
                item = methods.get(method.lower())
                if isinstance(item, dict):
                    operations.append(
                        {
                            "method": method,
                            "path": path,
                            "operation_id": item.get("operationId"),
                            "parameters": [
                                p.get("name", p.get("$ref"))
                                for p in methods.get("parameters", [])
                                + item.get("parameters", [])
                            ],
                            "responses": sorted(map(str, item.get("responses", {}))),
                            "request_media": list(
                                item.get("requestBody", {}).get("content", {})
                            ),
                        }
                    )
    print(json.dumps(operations, ensure_ascii=False, indent=2))
