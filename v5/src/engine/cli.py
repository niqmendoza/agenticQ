"""Interfaz de línea de comandos del motor documental."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import time

from brain import (
    Budget,
    VERSION,
    atomic,
    checked,
    doc_info,
    dump,
    index,
    outside,
    pack,
    session_load,
    show,
    verify,
)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--session")
    p.add_argument("--log-dir")
    sub = p.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("index")
    x.add_argument("corpus")
    x = sub.add_parser("pack")
    x.add_argument("--queries-json", required=True)
    x.add_argument("--seeds", type=int, default=2)
    x.add_argument("--related", type=int, default=5)
    x.add_argument("--max-docs", type=int, default=20)
    x.add_argument("--max-lines", type=int, default=120)
    x.add_argument("--replay", action="store_true")
    x = sub.add_parser("show")
    x.add_argument("path")
    x.add_argument("--start", type=int, default=1)
    x.add_argument("--end", type=int)
    x.add_argument("--max-lines", type=int, default=120)
    x.add_argument("--replay", action="store_true")
    x = sub.add_parser("headings")
    x.add_argument("path")
    x = sub.add_parser("links")
    x.add_argument("path")
    x.add_argument("--offset", type=int, default=0)
    x.add_argument("--limit", type=int, default=12)
    x = sub.add_parser("verify")
    x.add_argument("result_json")
    x.add_argument("--save")
    x.add_argument("--requirements-json")
    sub.add_parser("status")
    for x in [sub.choices["pack"], sub.choices["show"]]:
        x.add_argument("--max-chars", type=int, default=50000)
        x.add_argument("--max-tokens", type=int)
    a = p.parse_args()
    tick = time.perf_counter()
    started = datetime.now(timezone.utc).isoformat()
    code = 0
    s = None
    root = None
    c = None
    try:
        if a.cmd == "index":
            root = Path(a.corpus).resolve()
        else:
            c, cfg, settings = checked(a.db)
            root = Path(cfg["root"])
        for candidate in [a.db, a.session, a.log_dir, getattr(a, "save", None)]:
            if candidate:
                outside(candidate, root)
        if a.cmd == "index":
            result = index(root, a.db)
        else:
            s = session_load(a.session, cfg["revision"])
            if a.cmd in ("pack", "show") and not a.session:
                raise ValueError("pack/show necesitan --session fuera del corpus")
            if a.cmd == "pack":
                if (
                    not 1 <= a.seeds <= 10
                    or not 0 <= a.related <= 30
                    or not 1 <= a.max_docs <= 100
                    or not 1 <= a.max_lines <= 500
                ):
                    raise ValueError("Límites inválidos de pack")
                queries = json.loads(Path(a.queries_json).read_text())
                if (
                    not isinstance(queries, list)
                    or not queries
                    or not all(isinstance(q, str) and len(q) <= 2000 for q in queries)
                    or len(queries) > 20
                ):
                    raise ValueError(
                        "queries-json debe contener 1..20 preguntas de hasta 2000 caracteres"
                    )
                result = pack(
                    c,
                    cfg,
                    settings,
                    s,
                    queries,
                    Budget(a.max_chars, a.max_tokens),
                    a.seeds,
                    a.related,
                    a.max_docs,
                    a.max_lines,
                    a.replay,
                )
            elif a.cmd == "show":
                if not 1 <= a.max_lines <= 500:
                    raise ValueError("max-lines 1..500")
                result = show(
                    c,
                    cfg,
                    s,
                    a.path,
                    a.start,
                    a.end,
                    a.max_lines,
                    Budget(a.max_chars, a.max_tokens),
                    a.replay,
                )
            elif a.cmd == "headings":
                doc_info(c, a.path)
                result = {
                    "path": a.path,
                    "sections": [
                        dict(r)
                        for r in c.execute(
                            "SELECT start,end,title FROM headers WHERE path=?",
                            (a.path,),
                        )
                    ],
                    "notice": "Encabezados desde el parser del índice, sin releer cuerpos al modelo",
                }
            elif a.cmd == "links":
                doc_info(c, a.path)
                if a.offset < 0 or not 1 <= a.limit <= 100:
                    raise ValueError("offset >=0; limit 1..100")
                links = [
                    dict(r)
                    for r in c.execute(
                        "SELECT target,line,fragment FROM edges WHERE source=? ORDER BY line",
                        (a.path,),
                    )
                ]
                unresolved = [
                    json.loads(r[0])
                    for r in c.execute(
                        "SELECT data FROM unresolved WHERE source=?", (a.path,)
                    )
                ]
                items = links + unresolved
                result = {
                    "path": a.path,
                    "total": len(items),
                    "links": items[a.offset : a.offset + a.limit],
                    "next_offset": (
                        a.offset + a.limit if a.offset + a.limit < len(items) else None
                    ),
                }
            elif a.cmd == "verify":
                requirements = (
                    json.loads(Path(a.requirements_json).read_text())
                    if a.requirements_json
                    else None
                )
                result = verify(
                    c, cfg, s, json.loads(Path(a.result_json).read_text()), requirements
                )
                if a.save:
                    atomic(a.save, result)
            else:
                result = {
                    "version": VERSION,
                    "revision": cfg["revision"],
                    "documents": c.execute("SELECT count(*) FROM docs").fetchone()[0],
                    "fresh": True,
                    "session_documents": len(s["delivered"]),
                }
        if s is not None and a.session and a.cmd in ("pack", "show"):
            atomic(a.session, s)
    except (ValueError, OSError, sqlite3.Error, json.JSONDecodeError) as e:
        result = {
            "error": str(e),
            "action": "Revisar límites, rutas o reindexar; no continuar con contexto obsoleto",
        }
        code = 2
    if c is not None:
        c.close()
    output = dump(result)
    if a.log_dir and root is not None:
        try:
            outside(a.log_dir, root)
            d = Path(a.log_dir)
            d.mkdir(parents=True, exist_ok=True)
            n = (
                max([int(x.name.split(".")[0]) for x in d.glob("*.call.json")] + [0])
                + 1
            )
            atomic(
                d / f"{n:03}.call.json",
                {
                    "argv": sys.argv,
                    "started_utc": started,
                    "finished_utc": datetime.now(timezone.utc).isoformat(),
                    "local_seconds": time.perf_counter() - tick,
                    "exit_code": code,
                },
            )
            (d / f"{n:03}.result.json").write_text(output)
        except (ValueError, OSError) as e:
            print(dump({"error": str(e)}), end="")
            return 2
    print(output, end="")
    return code
