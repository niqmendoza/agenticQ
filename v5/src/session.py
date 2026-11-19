"""Persistencia local de una corrida con un solo escritor."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".trabajo"
RESULTS = ROOT / "resultados"
TEMPLATES = ROOT / "templates"
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
    if meta.get("schema") != "qa-run/3":
        raise ValueError("La sesión debe haber sido creada con el CLI de V5.")
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
