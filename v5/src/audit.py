"""Revisión transversal de intentos, evidencias y requisitos del alcance."""

from collections import Counter

from contracts import validate_execution
from records import validate_finding
from session import evidence_file, pending_browser_flows, read_json
from token_meter import token_report

STATES = (
    "passed",
    "failed",
    "blocked",
    "partial",
    "not_run",
    "unattempted",
    "invalid_evidence",
)


def inspect(run, meta, events):
    cases = {event["id"]: event for event in events if event["kind"] == "case"}
    attempts = {case_id: [] for case_id in cases}
    findings = []
    issues = []
    evidence = {}
    invalid = set()
    invalid_findings = set()

    for number, event in enumerate(events, 1):
        if event["kind"] == "execution":
            case_id = event["case_id"]
            attempts[case_id].append((number, event))
            try:
                validate_execution(run, meta["profile"], cases[case_id], event)
            except (ValueError, OSError) as error:
                invalid.add(number)
                issues.append(f"{case_id}, evento {number} · {error}")
        elif event["kind"] == "finding":
            findings.append(event)
            try:
                validate_finding(run, event, cases)
            except (ValueError, OSError) as error:
                invalid_findings.add(event["id"])
                issues.append(f"{event['id']} · {error}")

        for item in (
            (event, *event.get("results", []))
            if event["kind"] == "execution"
            else (event,)
        ):
            if "evidence" not in item:
                continue
            reference = item["evidence"]
            try:
                evidence[reference] = evidence_file(run, reference)
            except (ValueError, OSError) as error:
                issues.append(f"Evento {number} · {error}")

    def state(attempt):
        number, event = attempt
        return "invalid_evidence" if number in invalid else event["status"]

    first = {
        key: state(items[0]) if items else "unattempted"
        for key, items in attempts.items()
    }
    latest = {
        key: state(items[-1]) if items else "unattempted"
        for key, items in attempts.items()
    }
    groups = {}
    for case_id, case in cases.items():
        groups.setdefault(case["requirement"], []).append(case_id)

    plan_path = run / "plan.json"
    plan = read_json(plan_path) if plan_path.is_file() else None
    catalog = plan["catalog"] if plan is not None else None
    browser_ready = next(
        (
            event["browser_ready"]
            for event in reversed(events)
            if "browser_ready" in event
        ),
        None,
    )
    return {
        "browser_blocked": browser_ready is False,
        "tokens": token_report(run, meta, events),
        "missing_browser_flows": pending_browser_flows(plan or {}, events, latest),
        "cases": cases,
        "attempts": attempts,
        "findings": findings,
        "first": first,
        "latest": latest,
        "first_counts": Counter(first.values()),
        "latest_counts": Counter(latest.values()),
        "issues": list(dict.fromkeys(issues)),
        "invalid_attempts": invalid,
        "invalid_findings": invalid_findings,
        "evidence": evidence,
        "groups": groups,
        "plan": plan,
        "catalog": catalog,
    }


def publication_code(report):
    if report["issues"]:
        return 1
    tokens_blocked = report["tokens"] and report["tokens"]["blocked"]
    return (
        3
        if report["browser_blocked"]
        or report["missing_browser_flows"]
        or tokens_blocked
        else 0
    )
