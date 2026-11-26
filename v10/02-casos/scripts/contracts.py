"""Contratos de diseño de casos y ejecución del harness."""

from datetime import datetime

from session import evidence_file

ATTEMPT_CLASSES = ("product", "environment", "runner", "inconclusive")
BROWSER_FLOWS = {"web_ui": "Interfaz web", "swagger_ui": "Swagger UI"}


def required_text(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} debe ser un texto no vacío.")
    return value


def string_list(data, key, allow_empty=False):
    values = data.get(key)
    if (
        not isinstance(values, list)
        or not values
        and not allow_empty
        or not all(isinstance(value, str) and value.strip() for value in values)
    ):
        raise ValueError(f"{key} debe ser una lista de textos.")
    return values


def criteria_by_id(items):
    if not isinstance(items, list) or not items:
        raise ValueError("Se requiere una lista de criterios.")
    result = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Cada criterio debe ser un objeto.")
        identifier = required_text(item, "id")
        if identifier in result:
            raise ValueError(f"Criterio duplicado: {identifier}")
        result[identifier] = item
    return result


def valid_sources(sources):
    return isinstance(sources, list) and all(
        isinstance(source, dict)
        and isinstance(source.get("path"), str)
        and source["path"].strip()
        and (
            isinstance(source.get("locator"), str)
            and source["locator"].strip()
            or type(source.get("start")) is int
            and type(source.get("end")) is int
            and 1 <= source["start"] <= source["end"]
        )
        for source in sources
    )


def validate_case(case):
    for key in ("title", "feature", "requirement", "level", "scenario", "expected"):
        required_text(case, key)
    if case.get("priority") not in ("critical", "high", "medium", "low"):
        raise ValueError("priority debe ser critical, high, medium o low.")
    string_list(case, "preconditions", allow_empty=True)
    if "browser_flow" in case and case["browser_flow"] not in tuple(BROWSER_FLOWS):
        raise ValueError("browser_flow debe ser web_ui o swagger_ui.")
    steps = string_list(case, "steps")
    if "rationale" in case:
        required_text(case, "rationale")
    if "step_expected" in case:
        results = case["step_expected"]
        if (
            not isinstance(results, list)
            or len(results) != len(steps)
            or not all(isinstance(value, str) for value in results)
        ):
            raise ValueError("step_expected requiere un texto por cada paso de steps.")
    if "azure" in case:
        metadata = case["azure"]
        if not isinstance(metadata, dict):
            raise ValueError("azure debe ser un objeto de metadatos del caso.")
        for field in ("test_case_type", "functionality", "component_type", "type"):
            if field in metadata:
                required_text(metadata, field)
    oracle = case.get("oracle_status")
    if oracle not in ("documented", "inferred", "pending"):
        raise ValueError("oracle_status debe ser documented, inferred o pending.")
    if oracle == "pending":
        required_text(case, "oracle_pending_reason")
    if oracle == "inferred":
        required_text(case, "oracle_rationale")
    if not valid_sources(case.get("sources")) or (
        oracle == "documented" and not case["sources"]
    ):
        raise ValueError("Las fuentes necesitan path y locator o start/end.")
    for criterion in criteria_by_id(case.get("criteria")).values():
        required_text(criterion, "expected")


def validate_variants(cases):
    """Un caso por requisito, grupo, formato y variante declarados."""
    seen = set()
    for case in cases:
        variation = case.get("variante")
        if "variante" not in case:
            continue
        if not isinstance(variation, dict) or set(variation) != {"grupo", "formato", "tipo"}:
            raise ValueError("variante requiere grupo, formato y tipo.")
        group, fmt, kind = (required_text(variation, key) for key in ("grupo", "formato", "tipo"))
        key = (case["requirement"], group.casefold(), fmt.casefold().lstrip("."), kind.casefold())
        if not key[2] or key in seen:
            raise ValueError("El catálogo tiene un formato vacío o una variante duplicada.")
        seen.add(key)
        uploads = [step for step in case.get("browser_steps", []) if step["type"] == "upload"]
        checks = [criterion.get("check", {}) for criterion in case["criteria"]]
        if uploads and any(step["value"].rsplit(".", 1)[-1].casefold() != key[2] for step in uploads):
            raise ValueError("Los adjuntos deben coincidir con el formato de la variante.")
        if kind in {"limite_permitido", "limite_excedido"} and (
            len(uploads) != 1 or not any(
                check.get("type") in {"control_text", "control_contains"} and check.get("equals")
                for check in checks
            )
        ):
            raise ValueError("Cada variante de límite requiere un adjunto y un resultado visible específico.")
        if kind == "descarga" and not any(
            check.get("type") == "download_file" and check.get("contains")
            and check["extension"].lstrip(".").casefold() == key[2] for check in checks
        ):
            raise ValueError("La variante de descarga requiere comprobar el contenido del formato declarado.")


def derive_status(results):
    statuses = {item["status"] for item in results}
    if "failed" in statuses:
        return "failed"
    if statuses == {"passed"}:
        return "passed"
    if "passed" in statuses:
        return "partial"
    return "blocked" if "blocked" in statuses else "not_run"


def observed_time(value):
    if not isinstance(value, str):
        raise ValueError("La hora observada debe ser ISO 8601 con zona horaria.")
    time = datetime.fromisoformat(
        value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    )
    if time.tzinfo is None:
        raise ValueError("La hora observada debe incluir zona horaria.")
    return time


def validate_execution(run, profile, case, event):
    results = criteria_by_id(event.get("results"))
    if results.keys() != criteria_by_id(case["criteria"]).keys():
        raise ValueError("La ejecución requiere un resultado por criterio.")
    method = required_text(event, "execution_method")
    if method not in (
        "http",
        "api",
        "playwright",
        "mcp_db",
        "db",
        "cli",
        "suite",
        "manual",
        "other",
    ):
        raise ValueError("Método de ejecución desconocido.")
    if event.get("executor") not in ("runner", "agent", "human"):
        raise ValueError("executor debe ser runner, agent o human.")
    if "classification" in event and event["classification"] not in ATTEMPT_CLASSES:
        raise ValueError("classification inválida.")
    observed = any(r.get("status") in ("passed", "failed") for r in results.values())
    if observed and case.get("browser_flow") and method != "playwright":
        raise ValueError(
            "El recorrido requiere una ejecución interactiva de Playwright."
        )

    if (
        observed
        and method == "mcp_db"
        and event.get("db_source") not in profile.get("db_sources", [])
    ):
        raise ValueError("La fuente MCP debe estar declarada en el perfil.")
    for result in results.values():
        if result.get("status") not in ("passed", "failed", "blocked", "not_run"):
            raise ValueError("Estado de criterio inválido.")
        required_text(result, "observation")
        if result["status"] in ("passed", "failed") or "evidence" in result:
            evidence_file(run, result.get("evidence"))
    if "evidence" in event:
        evidence_file(run, event["evidence"])
    if event.get("status") != derive_status(results.values()):
        raise ValueError(
            "El estado del caso debe coincidir con sus resultados por criterio."
        )
    if case["oracle_status"] == "pending" and any(
        r["status"] in ("passed", "failed") for r in results.values()
    ):
        raise ValueError(
            "Un oráculo pendiente admite observaciones, sin veredictos por criterio."
        )
    start, end = event.get("started_at"), event.get("finished_at")
    if (observed or start is not None or end is not None) and observed_time(
        end
    ) < observed_time(start):
        raise ValueError("finished_at no puede ser anterior a started_at.")
    duration = event.get("duration_ms")
    if duration is not None and (type(duration) is not int or duration < 0):
        raise ValueError("duration_ms debe ser un entero no negativo o null.")
