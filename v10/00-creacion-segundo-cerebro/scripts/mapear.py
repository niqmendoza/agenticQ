"""Mapear una revisión Git y generar borradores normalizados por módulo."""

import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from higiene import sanear
from soporte import principal, read_json, write_json

from fichas import reusar
from perfil_qc import contiene, validar_perfil
from repositorio import SCHEMA, configurar, inventario, modulo, objetos, perfil_archivo, snapshot, texto_seguro


def opciones(parser):
    parser.add_argument("--perfil", type=Path, help="Perfil de aplicación para una publicación V3.")
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--app")
    parser.add_argument("--rev", help="Referencia Git local. Por defecto HEAD.")
    parser.add_argument("--modulos", type=Path, help="JSON de prefijos y dependencias para un monorepo.")
    parser.add_argument("--anterior", type=Path, help="Entrega previa para identificar módulos que necesitan revisión.")
    parser.add_argument("--max-kib-archivo", type=int, default=512)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def operar(args, salida, logs, resumen):
    """Crear un índice local redactado, un inventario técnico y fichas iniciales."""
    resumen["operacion"] = "mapear"
    perfil = None
    if args.perfil:
        if any((args.repo, args.app, args.rev, args.modulos)):
            raise ValueError("Con --perfil configurá repositorio, aplicación, revisión y módulos en el perfil.")
        raw_perfil = read_json(args.perfil)
        perfil = validar_perfil(raw_perfil)
        repo = args.perfil.resolve().parent / raw_perfil["repositorio"]
        app, revision, raw_config = perfil["aplicacion"], perfil["revision"], perfil["modulos"]
    else:
        if not args.repo or not args.app:
            raise ValueError("Indicá --perfil o bien --repo y --app.")
        repo, app, revision = args.repo, args.app.strip(), args.rev or "HEAD"
        raw_config = read_json(args.modulos) if args.modulos else {}
    if not app or len(app) > 160 or "\n" in app or sanear(app)[1]:
        raise ValueError("Indicá un nombre visible de aplicación válido, sin datos sensibles.")
    if not 1 <= args.max_kib_archivo <= 16384:
        raise ValueError("El tamaño máximo por archivo debe estar entre 1 y 16384 KiB.")
    deps, prefix = configurar(raw_config)
    commit, tree = snapshot(repo.resolve(), revision)
    resumen["commit"] = commit
    files, omisiones, huellas = inventario(tree, args.max_kib_archivo * 1024)
    por_modulo = defaultdict(list)
    for path, mode, oid in huellas:
        por_modulo[modulo(path, prefix, deps)].append([path.as_posix(), mode, oid])
    modulos, caracteres, redacciones = {}, 0, 0
    index = salida / "indice.sqlite"
    exclusiones = perfil["exclusiones"] if perfil else []
    with closing(sqlite3.connect(index)) as db, db, objetos(repo.resolve()) as leer:
        db.execute("CREATE TABLE metadata (schema TEXT NOT NULL, commit_sha TEXT NOT NULL)")
        db.execute("INSERT INTO metadata VALUES (?,?)", (SCHEMA, commit))
        db.execute("""CREATE TABLE archivos (
            ruta TEXT PRIMARY KEY, modulo TEXT NOT NULL, oid TEXT NOT NULL, tipo TEXT NOT NULL,
            lineas INTEGER NOT NULL, simbolos TEXT NOT NULL, texto TEXT NOT NULL
        )""")
        db.execute("CREATE INDEX archivos_por_modulo ON archivos(modulo, ruta)")
        for path, oid, size in files:
            ruta = path.as_posix()
            if any(contiene(ruta, excluido) for excluido in exclusiones):
                omisiones["perfil_excluido"] += 1
                continue
            if sanear(ruta)[1]:
                omisiones["ruta_sensible"] += 1
                continue
            blob = leer(oid, size)
            try:
                texto, ajustes = texto_seguro(blob)
            except ValueError as error:
                omisiones[str(error)] += 1
                continue
            if not texto.strip():
                omisiones["archivo_vacio"] += 1
                continue
            key = modulo(path, prefix, deps)
            tipo, simbolos = perfil_archivo(path, texto)
            archivo_hash = oid.decode("ascii")
            db.execute(
                "INSERT INTO archivos VALUES (?,?,?,?,?,?,?)",
                (ruta, key, archivo_hash, tipo, len(texto.split("\n")), json.dumps(simbolos, ensure_ascii=False), texto),
            )
            data = modulos.setdefault(key, {
                "tipos": Counter(),
            })
            data["tipos"][tipo] += 1
            caracteres += len(texto)
            redacciones += ajustes
    if not modulos:
        raise ValueError("El commit no contiene archivos de texto elegibles con esta configuración.")
    faltantes = deps.keys() - modulos.keys()
    if faltantes:
        raise ValueError("Los prefijos no tienen archivos elegibles para: " + ", ".join(sorted(faltantes)))
    borradores = salida / "borradores"
    borradores.mkdir()
    for key, data in sorted(modulos.items()):
        tipos = data.pop("tipos")
        data.update(
            cantidades=dict(sorted(tipos.items())),
            archivos=sum(tipos.values()),
            huella=digest(por_modulo[key]),
            depende_de=deps.get(key, []),
        )
        write_json(borradores / f"{key}.json", {"modulo": key, "hechos": [], "pendientes": []})
    mapa = {
        "schema": SCHEMA, "app": app, "commit": commit,
        "configuracion": digest([raw_config, args.max_kib_archivo, exclusiones]) if exclusiones else digest([raw_config, args.max_kib_archivo]),
        "huella_raiz": digest(por_modulo["raiz"]),
        "modulos": modulos, "omisiones": dict(sorted(omisiones.items())),
        "archivos_indexados": sum(data["archivos"] for data in modulos.values()),
        "caracteres_fuente": caracteres, "redacciones": redacciones,
        **({"perfil_qc": perfil} if perfil else {}),
    }
    with closing(sqlite3.connect(index)) as db:
        db.row_factory = sqlite3.Row
        previas, base = reusar(args.anterior, mapa, db)
    for key, data in modulos.items():
        data["revision"] = "reutilizable" if key in previas else "pendiente"
    mapa["commit_base"] = base
    write_json(salida / "mapa.json", mapa)
    resumen.update(
        operacion="mapear", commit=commit, modulos=len(modulos), redacciones=redacciones,
        archivos_indexados=sum(data["archivos"] for data in modulos.values()),
        caracteres_fuente=caracteres, omisiones=dict(sorted(omisiones.items())),
        modulos_reutilizables=len(previas), modulos_para_revisar=len(modulos) - len(previas),
    )
    print(f"{len(modulos)} módulos · {resumen['archivos_indexados']} archivos · commit {commit[:12]}")
    return 0


if __name__ == "__main__":
    principal(__file__, opciones, operar)
