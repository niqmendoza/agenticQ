"""Acceso de solo lectura al índice generado por la etapa 00."""

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

from repositorio import SCHEMA
from soporte import read_json


@contextmanager
def abrir_indice(folder):
    root = Path(folder).resolve()
    path = root / "indice.sqlite"
    if not path.is_file() or path.is_symlink() or (root / "mapa.json").is_symlink():
        raise ValueError("Indicá la carpeta con mapa.json e indice.sqlite publicada por mapear.py.")
    data = read_json(root / "mapa.json")
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA trusted_schema=OFF")
            meta = db.execute("SELECT schema,commit_sha FROM metadata").fetchone()
            if not meta or data.get("schema") != SCHEMA or tuple(meta) != (SCHEMA, data["commit"]):
                raise ValueError("El mapa y el índice deben pertenecer al mismo commit y versión del esquema.")
            yield data, db
    except sqlite3.Error as error:
        raise ValueError("El índice de código es inválido. Repetí el mapeo.") from error


def archivo(db, path):
    row = db.execute("SELECT * FROM archivos WHERE ruta=?", (path,)).fetchone()
    if row is None:
        raise ValueError("El archivo no forma parte del índice elegible.")
    return row
