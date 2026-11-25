"""Persistencia local de una corrida con un solo escritor."""

import json
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("QC_WORKSPACE", PACKAGE / "logs" / "qc")).resolve()
WORK = ROOT / ".trabajo"
RESULTS = ROOT / "resultados"
TEMPLATES = PACKAGE / "plantillas"
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}")


def run_id(value):
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(
            "Usá un ID de 1 a 80 caracteres con letras, números, guiones o guiones bajos."
        )
    return value


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def load(run):
    run = Path(run).resolve()
    meta = read_json(run / "run.json")
    if meta.get("schema") != "qa-run/6":
        raise ValueError("La sesión debe haber sido creada con una versión compatible del CLI.")
    return run, meta, read_json(run / "events.json")


def append(run, event):
    events = read_json(run / "events.json")
    events.append({"time_utc": timestamp(), **event})
    write_json(run / "events.json", events)


def evidence_file(run, reference):
    """Acepta referencias portables a notas de evidencia dentro de la sesión."""
    if not isinstance(reference, str) or not re.fullmatch(
        r"evidencias/[A-Za-z0-9][A-Za-z0-9_-]{0,159}\.md", reference
    ):
        raise ValueError(
            "La evidencia debe usar una ruta como evidencias/CASO-intento.md."
        )
    source = run / reference
    if (
        source.parent.is_symlink()
        or source.is_symlink()
        or not source.is_file()
        or not source.read_text(encoding="utf-8").strip()
    ):
        raise ValueError(f"Evidencia ausente o vacía: {reference}.")
    return source


def require_browser_ready(events):
    latest = next(
        (event for event in reversed(events) if "browser_ready" in event),
        {},
    )
    if (
        latest.get("browser_ready") is not True
        or latest.get("python") != sys.executable
    ):
        raise ValueError(
            "Playwright requiere preflight --browser exitoso con este Python. Avisá al usuario y detené la corrida."
        )


def pending_browser_flows(plan, events, latest=None):
    required = set(plan.get("browser_flows", []))
    cases = {
        event["id"]: event.get("browser_flow")
        for event in events
        if event["kind"] == "case"
    }
    if latest is None:
        latest = {
            event["case_id"]: event["status"]
            for event in events
            if event["kind"] == "execution"
        }
    exercised = {
        cases[key]
        for key, status in latest.items()
        if status in ("passed", "failed", "partial")
    }
    return sorted(required - exercised)


@contextmanager
def writer(run):
    locks = WORK / ".locks"
    locks.mkdir(parents=True, exist_ok=True)
    with (locks / run_id(run.name)).open("a+b") as handle:
        try:
            if os.name == "nt":
                import msvcrt

                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ValueError(
                "Otro proceso está usando esta corrida. Usá otro ID para un job independiente."
            ) from None
        yield
