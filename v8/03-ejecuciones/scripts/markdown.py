"""Formato Markdown para los registros y evidencias del harness."""

import re
from html import escape
from pathlib import Path


def inline(value):
    if value is None or value == "":
        return "—"
    value = escape(" ".join(str(value).splitlines()), quote=False)
    return re.sub(r"([\\`*_\[\]|#!~$])", r"\\\1", value)


def table(columns, rows):
    return [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
        *("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows),
        "",
    ]


def write_markdown(path, lines):
    Path(path).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def source_label(source):
    location = source.get("locator") or f"líneas {source['start']}–{source['end']}"
    revision = f" · revisión {source['revision']}" if source.get("revision") else ""
    return f"{source['path']} · {location}{revision}"
