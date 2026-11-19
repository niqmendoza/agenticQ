"""Validación y registro de casos, intentos, hallazgos y decisiones."""

import json
import sys

from contracts import (
    ATTEMPT_CLASSES,
    required_text,
    string_list,
    valid_sources,
    validate_case,
    validate_execution,
)
from session import (
    evidence_file,
    load,
    pending_browser_flows,
    read_json,
    require_browser_ready,
    run_id,
    timestamp,
    write_json,
)


def validate_finding(run, event, cases):
    for key in ("observation", "interpretation", "pending"):
        required_text(event, key)
    if event.get("confidence") not in ("confirmed", "hypothesis"):
        raise ValueError("confidence debe ser confirmed o hypothesis.")
    if event.get("classification") not in ATTEMPT_CLASSES:
        raise ValueError("classification inválida.")
    if set(string_list(event, "case_ids", allow_empty=True)) - cases.keys():
        raise ValueError("El hallazgo refiere a un caso sin registrar.")
    if event.get("fix_status", "open") not in ("open", "verified_fixed"):
        raise ValueError("fix_status debe ser open o verified_fixed.")
    if "sdd" in event:
        guidance = event["sdd"]
        if not isinstance(guidance, dict):
            raise ValueError("sdd debe contener los datos de la propuesta.")
        for field in ("component", "suggestion"):
            required_text(guidance, field)
        for field in ("acceptance", "regression"):
            string_list(guidance, field)
        for field in ("title", "expected", "impact", "evidence_summary"):
            if field in guidance:
                required_text(guidance, field)
        if "reproduction" in guidance:
            string_list(guidance, "reproduction")
        if not valid_sources(guidance.get("sources", [])):
            raise ValueError("Las fuentes SDD necesitan path y locator o start/end.")
    if event["confidence"] == "confirmed" or "evidence" in event:
        evidence_file(run, event.get("evidence"))


def store_records(run, meta, events, data):
    items = data if isinstance(data, list) else [data]
    if not items:
        raise ValueError("La lista de registros no puede estar vacía.")
    cases = {event["id"]: event for event in events if event["kind"] == "case"}
    findings = {event["id"] for event in events if event["kind"] == "finding"}
    pending = []
    for item in items:
        if not isinstance(item, dict) or item.get("kind") not in (
            "case",
            "execution",
            "finding",
            "note",
        ):
            raise ValueError(
                "Cada registro requiere kind: case, execution, finding o note."
            )
        if any(field in item for field in ("time_utc", "browser_ready", "python")):
            raise ValueError("El sistema asigna time_utc y los campos de preflight.")
        kind = item["kind"]
        if kind == "case":
            identifier = run_id(required_text(item, "id"))
            if identifier in cases:
                raise ValueError(f"Caso duplicado: {identifier}.")
            validate_case(item)
            cases[identifier] = item
        elif kind == "execution":
            identifier = required_text(item, "case_id")
            if identifier not in cases:
                raise ValueError(f"Caso sin registrar: {identifier}.")
            required_text(item, "observation")
            if not (run / "plan.json").is_file():
                raise ValueError("Congelá el plan antes de registrar un intento.")
            validate_execution(run, meta["profile"], cases[identifier], item)
            if item["status"] in ("passed", "failed", "partial"):
                plan = read_json(run / "plan.json")
                if item["execution_method"] in ("http", "playwright") and not plan.get(
                    "browser_flows"
                ):
                    raise ValueError(
                        "Creá un plan que incluya el recorrido Playwright de la web o Swagger."
                    )
                if plan.get("browser_flows"):
                    require_browser_ready(events)
                    if not cases[identifier].get(
                        "browser_flow"
                    ) and pending_browser_flows(plan, events + pending):
                        raise ValueError(
                            "Registrá primero los recorridos Playwright exigidos por el plan."
                        )
        elif kind == "finding":
            identifier = run_id(required_text(item, "id"))
            if identifier in findings:
                raise ValueError(f"Hallazgo duplicado: {identifier}.")
            validate_finding(run, item, cases)
            findings.add(identifier)
        else:
            required_text(item, "phase")
            required_text(item, "observation")
            if "evidence" in item:
                evidence_file(run, item["evidence"])
        pending.append({"time_utc": timestamp(), **item})
    write_json(run / "events.json", events + pending)


def record(args):
    run, meta, events = load(args.run)
    data = json.load(sys.stdin) if args.json == "-" else read_json(args.json)
    store_records(run, meta, events, data)
    print("Registros guardados.")
