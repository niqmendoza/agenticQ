"""Contratos de casos y resultados para sesiones qa-run/2."""

from datetime import datetime
from pathlib import Path


def required_text(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} debe ser un texto no vacío.")
    return value


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


def validate_case(case):
    required_text(case, "requirement")
    if (
        not isinstance(case.get("steps"), list)
        or not case["steps"]
        or not all(isinstance(step, str) and step.strip() for step in case["steps"])
    ):
        raise ValueError("steps debe contener los pasos funcionales del caso.")
    if case["oracle_status"] == "pending":
        required_text(case, "oracle_pending_reason")
    if case["oracle_status"] == "documented":
        sources = case["sources"]
        if not isinstance(sources, list) or not all(
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
        ):
            raise ValueError(
                "Cada fuente documentada necesita path y locator o start/end."
            )
    for criterion in criteria_by_id(case.get("criteria")).values():
        required_text(criterion, "expected")


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
    criteria = criteria_by_id(case.get("criteria"))
    if results.keys() != criteria.keys():
        raise ValueError(
            "La ejecución debe registrar un resultado por cada criterio del caso."
        )
    method = required_text(event, "execution_method")
    if method not in {"http", "playwright", "mcp_db", "manual"}:
        raise ValueError("Método de ejecución desconocido.")
    if method == "mcp_db" and any(
        r.get("status") in ("passed", "failed") for r in results.values()
    ):
        if event.get("db_source") not in profile.get("db_sources", []):
            raise ValueError("La fuente MCP debe estar declarada en el perfil.")
    for result in results.values():
        if result.get("status") not in ("passed", "failed", "blocked", "not_run"):
            raise ValueError("Estado de criterio inválido.")
        required_text(result, "observation")
        if result["status"] in ("passed", "failed"):
            evidence = Path(required_text(result, "evidence"))
            resolved = (run / evidence).resolve()
            if (
                evidence.is_absolute()
                or run not in resolved.parents
                or not resolved.is_file()
            ):
                raise ValueError(
                    "La evidencia debe ser un archivo existente dentro de la sesión."
                )
    if event["status"] != derive_status(results.values()):
        raise ValueError(
            "El estado del caso debe coincidir con sus resultados por criterio."
        )
    if case["oracle_status"] == "pending" and "passed" in {
        r["status"] for r in results.values()
    }:
        raise ValueError("Un oráculo pendiente no admite criterios aprobados.")
    start, end = event.get("started_at"), event.get("finished_at")
    if (
        start is not None
        or end is not None
        or any(result["status"] in ("passed", "failed") for result in results.values())
    ):
        if observed_time(end) < observed_time(start):
            raise ValueError("finished_at no puede ser anterior a started_at.")
    duration = event.get("duration_ms")
    if duration is not None and (type(duration) is not int or duration < 0):
        raise ValueError("duration_ms debe ser un entero no negativo o null.")
