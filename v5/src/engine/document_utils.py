#!/usr/bin/env python3
"""Indexación y resolución de documentos locales para el motor de contexto."""
import collections
import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlparse

EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".csv",
    ".tsv",
    ".html",
    ".xml",
}
STOP = set(
    "a al con de del el en es la las lo los o para por que se un una y the of to and in is for on with from".split()
)
SCHEMA = 1


def sha(b):
    return hashlib.sha256(b).hexdigest()


def norm(s):
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", s.casefold())
        if not unicodedata.combining(c)
    )


def words(s):
    return [w for w in re.findall(r"\w+", norm(s)) if len(w) > 1 and w not in STOP]


def scan(root):
    rows = []
    excluded = []
    if not root.is_dir():
        raise ValueError("El corpus no es un directorio")
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            excluded.append(
                {"path": p.relative_to(root).as_posix(), "reason": "symlink no seguido"}
            )
            continue
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if p.suffix.lower() not in EXTENSIONS:
            excluded.append({"path": rel, "reason": "extensión excluida"})
            continue
        b = p.read_bytes()
        try:
            text = b.decode("utf-8")
            if "\0" in text:
                raise ValueError()
        except (UnicodeDecodeError, ValueError):
            excluded.append({"path": rel, "reason": "no UTF-8 o NUL"})
            continue
        rows.append({"path": rel, "sha256": sha(b), "bytes": len(b), "text": text})
    return rows, excluded


def metadata(lines):
    # Preserva valores YAML crudos; no presume ontología ni interpreta YAML complejo.
    meta = {}
    end = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                end = i + 1
                break
        if end:
            meta["frontmatter_raw"] = "\n".join(lines[:end])
            for line in lines[1 : end - 1]:
                m = re.match(r"^([\w-]+):\s*(.*)$", line)
                if m:
                    meta[m[1]] = m[2].strip().strip("\"'")
    return meta, end


def sections(text, max_lines=40):
    lines = text.splitlines()
    meta, start = metadata(lines)
    head = "Documento"
    begin = 1
    fence = None
    spans = []
    for i, line in enumerate(lines, 1):
        if i <= start:
            continue
        fm = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fm:
            c = fm[1][0]
            if fence == c:
                fence = None
            elif fence is None:
                fence = c
        if fence is None and re.match(r"^#{1,6}\s+", line):
            if begin < i:
                spans.append((begin, i - 1, head))
            begin = i
            head = re.sub(r"^#+\s+", "", line)
    if lines:
        spans.append((begin, len(lines), head))
    result = []
    for a, b, title in spans:
        while a <= b:
            e = min(a + max_lines - 1, b)
            result.append((a, e, title, "\n".join(lines[a - 1 : e])))
            if e == b:
                break
            a = e - 3  # overlap verificable, sin perder líneas
    return meta, result


def links(path, text):
    for m in re.finditer(r"\[\[([^\]]+)\]\]|\[[^\]]*\]\(([^)]+)\)", text):
        raw = (m[1] or m[2]).split("|")[0]
        u = urlparse(raw)
        if u.scheme or raw.startswith("//"):
            continue
        yield {
            "target": unquote(raw.split("#")[0]),
            "fragment": unquote(raw.split("#", 1)[1]) if "#" in raw else "",
            "line": text[: m.start()].count("\n") + 1,
            "kind": "wiki" if m[1] else "markdown",
        }


def connect(db):
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    return c


def index(root, db):
    root = Path(root).resolve()
    db = Path(db).resolve()
    if root == db or root in db.parents:
        raise ValueError("Guardar índice fuera del corpus")
    rows, excluded = scan(root)
    db.parent.mkdir(parents=True, exist_ok=True)
    c = connect(db)
    with c:
        c.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY,value TEXT)")
        c.execute(
            "CREATE TABLE IF NOT EXISTS docs (path TEXT PRIMARY KEY,sha TEXT,bytes INTEGER,text TEXT,meta TEXT)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS chunks (path TEXT,start INTEGER,end INTEGER,section TEXT,text TEXT)"
        )
        c.execute("CREATE TABLE IF NOT EXISTS links (path TEXT,data TEXT)")
        old = dict(c.execute("SELECT key,value FROM config").fetchall())
        if old and (old.get("root") != str(root) or old.get("schema") != str(SCHEMA)):
            raise ValueError("Índice de otra raíz/versión: use otra ruta de DB")
        previous = {r["path"]: r["sha"] for r in c.execute("SELECT path,sha FROM docs")}
        changed = 0
        removed = 0
        current = {r["path"] for r in rows}
        for p in set(previous) - current:
            for table in ("docs", "chunks", "links"):
                c.execute(f"DELETE FROM {table} WHERE path=?", (p,))
            removed += 1
        for r in rows:
            if previous.get(r["path"]) == r["sha256"]:
                continue
            changed += 1
            meta, ch = sections(r["text"])
            for table in ("docs", "chunks", "links"):
                c.execute(f"DELETE FROM {table} WHERE path=?", (r["path"],))
            c.execute(
                "INSERT INTO docs VALUES(?,?,?,?,?)",
                (
                    r["path"],
                    r["sha256"],
                    r["bytes"],
                    r["text"],
                    json.dumps(meta, ensure_ascii=False),
                ),
            )
            c.executemany(
                "INSERT INTO chunks VALUES(?,?,?,?,?)", [(r["path"], *x) for x in ch]
            )
            c.executemany(
                "INSERT INTO links VALUES(?,?)",
                [
                    (r["path"], json.dumps(x, ensure_ascii=False))
                    for x in links(r["path"], r["text"])
                ],
            )
        revision = sha(
            json.dumps(
                [(r["path"], r["sha256"]) for r in rows], ensure_ascii=False
            ).encode()
        )
        cfg = {
            "root": str(root),
            "revision": revision,
            "schema": str(SCHEMA),
            "excluded": json.dumps(excluded, ensure_ascii=False),
        }
        c.executemany("INSERT OR REPLACE INTO config VALUES(?,?)", cfg.items())
    result = {
        "revision": revision,
        "documents": len(rows),
        "chunks": c.execute("SELECT count(*) FROM chunks").fetchone()[0],
        "changed": changed,
        "removed": removed,
        "unchanged": len(rows) - changed,
        "excluded": excluded,
        "index_bytes": db.stat().st_size,
    }
    c.close()
    return result


def checked(db):
    if not Path(db).is_file():
        raise ValueError("Falta índice: ejecutar index")
    c = connect(db)
    cfg = dict(c.execute("SELECT key,value FROM config").fetchall())
    if cfg.get("schema") != str(SCHEMA):
        raise ValueError("Versión de índice incompatible")
    current, _ = scan(Path(cfg["root"]))
    actual = {r["path"]: r["sha256"] for r in current}
    stored = {r["path"]: r["sha"] for r in c.execute("SELECT path,sha FROM docs")}
    if actual != stored:
        c.close()
        raise ValueError(
            "Índice desactualizado (hash/altas/bajas): volver a ejecutar index"
        )
    return c, cfg


def relation_index(c):
    """Construir una vez el índice de nombres utilizado al resolver enlaces."""
    docs = list(c.execute("SELECT path,meta FROM docs"))
    names = collections.defaultdict(set)
    for d in docs:
        p = Path(d["path"])
        m = json.loads(d["meta"])
        for key in [p.stem, d["path"], m.get("title", "")]:
            if key:
                names[norm(key)].add(d["path"])
        for a in m.get("aliases", "").strip("[]").split(","):
            if a.strip():
                names[norm(a.strip().strip("\"'"))].add(d["path"])
    return {d["path"] for d in docs}, names


def relations(c, path, lookup=None):
    paths, names = lookup if lookup is not None else relation_index(c)
    result = []
    for r in c.execute("SELECT data FROM links WHERE path=?", (path,)):
        l = json.loads(r[0])
        target = l["target"]
        if l["kind"] == "markdown":
            # Normalizar ../ sin permitir escapes de raíz ni resolver archivos externos.
            parts = []
            for part in (Path(path).parent / target).parts:
                if part == "..":
                    if parts:
                        parts.pop()
                    else:
                        parts = ["__outside__"]
                        break
                elif part != ".":
                    parts.append(part)
            candidate = "/".join(parts)
            matches = {candidate} if candidate in paths else set()
        else:
            matches = names.get(norm(target), set()) | names.get(
                norm(Path(target).stem), set()
            )
        l.update(
            resolved=sorted(matches), ambiguous=len(matches) > 1, missing=not matches
        )
        result.append(l)
    return result
