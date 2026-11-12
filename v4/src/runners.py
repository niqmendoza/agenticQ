"""Ejecutores funcionales HTTP y Playwright. Solo guardan resultados de aserciones."""

import json
import os
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4

from contracts import criteria_by_id, derive_status
from json_tools import JSON_TYPES, json_at, valid_path
from records import store_records
from session import load, read_json, timestamp, write_json
from ui_walk import inspect_page, run_walk, walk_plan

HTTP_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
MAX_BODY = 2 * 1024 * 1024


class Unavailable(Exception):
    pass


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


def validate_profile(profile):
    if not isinstance(profile, dict) or not isinstance(profile.get("base_url"), str):
        raise ValueError("El perfil requiere base_url.")
    parts = urlsplit(profile["base_url"])
    if (
        parts.scheme not in ("http", "https")
        or not parts.hostname
        or parts.username is not None
        or (parts.path not in ("", "/") or parts.query or parts.fragment)
    ):
        raise ValueError(
            "base_url debe ser un origen HTTP(S) sin ruta ni credenciales."
        )
    origin(profile["base_url"])
    if "browser_channel" in profile and profile["browser_channel"] not in (
        "chrome",
        "msedge",
        "chromium",
    ):
        raise ValueError("browser_channel debe ser chrome, msedge o chromium.")
    for key in ("http_operations", "browser_paths", "db_sources"):
        if not isinstance(profile.get(key, []), list):
            raise ValueError(f"{key} debe ser una lista.")
    for op in profile.get("http_operations", []):
        if not isinstance(op, dict) or op.get("method") not in HTTP_METHODS:
            raise ValueError("Cada operación HTTP necesita un método válido.")
        target_path(op.get("path"))
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
    if "bearer_env" in profile and (
        not isinstance(profile["bearer_env"], str)
        or not profile["bearer_env"].isidentifier()
    ):
        raise ValueError("bearer_env debe ser el nombre de una variable de entorno.")


def checks_for(case, method):
    checks = {}
    for identifier, criterion in criteria_by_id(case["criteria"]).items():
        check = criterion.get("check")
        if not isinstance(check, dict):
            raise ValueError(f"Falta check ejecutable para {identifier}.")
        kind, expected = check.get("type"), check.get("equals")
        valid = (
            kind == "status"
            and type(expected) is int
            and 100 <= expected <= 599
            or method == "http"
            and kind == "content_type"
            and isinstance(expected, str)
            and bool(expected)
            or method == "http"
            and kind in ("json_equals", "json_type")
            and "equals" in check
            and valid_path(check.get("path"))
            and (
                kind == "json_equals"
                or isinstance(expected, str)
                and expected in JSON_TYPES
            )
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


def http_request(profile, operation, checks, fixture):
    method, path = operation["method"], operation["path"]
    headers = {"Accept": "application/json"}
    if fixture is not None:
        headers["Content-Type"] = "application/json"
    if operation.get("authenticated", False):
        token = os.environ.get(profile.get("bearer_env", ""))
        if not token:
            raise Unavailable("Falta la credencial configurada para el caso.")
        headers["Authorization"] = "Bearer " + token
    request = Request(
        profile["base_url"].rstrip("/") + path,
        data=fixture,
        method=method,
        headers=headers,
    )
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        response = opener.open(request, timeout=15)
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
            if any(c["type"] in ("json_equals", "json_type") for c in checks.values())
            else b""
        )
    data = None
    if (
        len(body) <= MAX_BODY
        and media_type
        and (media_type == "application/json" or media_type.endswith("+json"))
    ):
        try:
            data = json.loads(body)
        except (ValueError, UnicodeError):
            pass
    results = {}
    for identifier, check in checks.items():
        kind = check["type"]
        if kind == "status":
            results[identifier] = status == check["equals"]
        elif kind == "content_type":
            results[identifier] = media_type == check["equals"]
        else:
            try:
                value = json_at(data, check["path"])
            except (KeyError, IndexError):
                results[identifier] = False
            else:
                results[identifier] = (
                    type(value) in JSON_TYPES[check["equals"]]
                    if kind == "json_type"
                    else type(value) is type(check["equals"])
                    and value == check["equals"]
                )
    return results, {"http_status": status, "content_type": media_type}


def browser_request(profile, path, checks, config=None, plan=None):
    try:
        from playwright.sync_api import (
            Error,
            TimeoutError as PlaywrightTimeout,
            sync_playwright,
        )
    except ImportError:
        raise Unavailable("Playwright para Python no está instalado.") from None
    target = origin(profile["base_url"])
    with sync_playwright() as playwright:
        try:
            options = (
                {"channel": profile["browser_channel"]}
                if "browser_channel" in profile
                else {}
            )
            browser = playwright.chromium.launch(**options)
        except Error:
            raise Unavailable("Chromium de Playwright no pudo iniciarse.") from None
        try:
            page = browser.new_page(service_workers="block")
            errors = []
            if config is not None:
                page.on("pageerror", lambda _: errors.append(True))

            def route_request(route):
                request = route.request
                same_origin = origin(request.url) == target
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
                if request.method in ("GET", "HEAD") and (
                    same_origin or approved_asset
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
                            headers=headers, max_redirects=0, timeout=15000
                        )
                    except Error:
                        route.abort()
                        return
                    if 300 <= fetched.status < 400:
                        route.abort()
                    else:
                        route.fulfill(response=fetched)
                else:
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
        finally:
            browser.close()


def run_case(args):
    run, meta, events = load(args.run)
    if meta["schema"] != "qa-run/2":
        raise ValueError("execute requiere una sesión creada con --profile.")
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
    method = args.via
    checks = checks_for(case, method)
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
    if method == "http":
        op = case.get("http")
        if not isinstance(op, dict) or not isinstance(
            op.get("authenticated", False), bool
        ):
            raise ValueError(
                "El caso HTTP requiere http con método, ruta y autenticación opcional."
            )
        path = target_path(op.get("path"))
        if not any(
            item["method"] == op.get("method") and item["path"] == path
            for item in profile.get("http_operations", [])
        ):
            raise ValueError("Método y ruta fuera del perfil de ejecución.")
        if args.body:
            if op["method"] in ("GET", "HEAD"):
                raise ValueError("El caso GET/HEAD no admite --body.")
            with Path(args.body).open("rb") as body_file:
                fixture = body_file.read(MAX_BODY + 1)
            if len(fixture) > MAX_BODY:
                raise ValueError("El fixture JSON supera el límite.")
            json.loads(fixture)
    else:
        path = target_path(case.get("browser_path"))
        if path not in profile.get("browser_paths", []) or args.body:
            raise ValueError(
                "Ruta de navegador fuera del perfil o --body incompatible."
            )
    if case["oracle_status"] == "pending":
        raise ValueError("Resolver el oráculo antes de ejecutar el caso.")

    started, tick = timestamp(), perf_counter()
    evidence_path = Path("evidencias") / f"{uuid4().hex}.json"
    try:
        verdicts, metadata = (
            http_request(profile, op, checks, fixture)
            if method == "http"
            else browser_request(profile, path, checks, config, plan)
        )
    except (Unavailable, URLError, OSError) as error:
        reason = (
            str(error)
            if isinstance(error, Unavailable)
            else "La conexión o lectura del entorno no se completó."
        )
        verdicts, metadata = None, {"blocked_reason": reason}
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
                    "Coincide con lo esperado."
                    if verdicts[identifier]
                    else "Difiere de lo esperado."
                )
                if verdicts is not None
                else metadata["blocked_reason"]
            ),
            "evidence": evidence_path.as_posix(),
        }
        for identifier in checks
    ]
    status = derive_status(results)
    (run / evidence_path.parent).mkdir(exist_ok=True)
    write_json(
        run / evidence_path,
        {
            "case_id": args.case,
            "execution_method": method,
            "results": results,
            **metadata,
        },
    )
    store_records(
        run,
        meta,
        events,
        {
            "kind": "execution",
            "case_id": args.case,
            "status": status,
            "observation": f"Resultado de {len(results)} aserciones: {status}.",
            "evidence": evidence_path.as_posix(),
            "execution_method": method,
            "results": results,
            "started_at": started,
            "finished_at": finished,
            "duration_ms": duration,
        },
    )
    print(run / evidence_path)
    return {"passed": 0, "failed": 1, "blocked": 3}[status]


def inventory(args):
    spec = read_json(args.spec)
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
                        }
                    )
    print(json.dumps(operations, ensure_ascii=False, indent=2))
