"""Publicar un segundo cerebro estándar con citas verificadas y módulos reutilizables."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from soporte import abrir, principal, read_json, write_json

from fichas import reusar, validar
from indice import abrir_indice
from okf import VERSION_OKF, publicar_okf
from repositorio import SCHEMA


def opciones(parser):
    parser.add_argument("--mapa", required=True, type=Path)
    parser.add_argument("--revision", action="append", type=Path, default=[], help="Ficha revisada. Se puede repetir.")
    parser.add_argument("--anterior", type=Path, help="Entrega de un segundo cerebro previo de la misma aplicación.")


def operar(args, salida, logs, resumen):
    """Publicar un bundle OKF v0.2 indexable por la etapa 01."""
    resumen["operacion"] = "publicar"
    abrir(args.mapa.resolve(), "00-creacion-segundo-cerebro", requiere="indice.sqlite")
    cache, revisadas = {}, {}
    with abrir_indice(args.mapa) as (mapa, db):
        resumen["commit"] = mapa["commit"]
        previas, base = reusar(args.anterior, mapa, db)
        for path in args.revision:
            ficha = read_json(path)
            key = ficha.get("modulo")
            if key not in mapa["modulos"] or key in revisadas:
                raise ValueError("Cada ficha debe referir a un módulo único del mapa.")
            revisadas[key] = validar(ficha, key, db, cache)
        fichas, estados = {}, {}
        for key in sorted(mapa["modulos"]):
            if key in revisadas:
                fichas[key] = revisadas[key]
                estados[key] = "revisado"
            elif key in previas:
                fichas[key] = validar(previas[key], key, db, cache)
                estados[key] = "reutilizado"
            else:
                fichas[key] = {
                    "modulo": key, "hechos": [],
                    "pendientes": ["Falta revisar este módulo y vincular sus reglas con evidencia."],
                }
                estados[key] = "pendiente"
    corpus = salida / "corpus"
    relaciones_pendientes = publicar_okf(corpus, mapa, fichas)
    n_hechos = sum(len(ficha["hechos"]) for ficha in fichas.values())
    n_pendientes = sum(len(ficha["pendientes"]) for ficha in fichas.values()) + len(relaciones_pendientes)
    write_json(salida / "fichas.json", fichas)
    write_json(salida / "manifiesto.json", {
        "schema": SCHEMA, "app": mapa["app"], "commit": mapa["commit"], "commit_base": base,
        "configuracion": mapa["configuracion"], "corpus": "corpus", "okf_version": VERSION_OKF,
        "huella_raiz": mapa["huella_raiz"],
        "modulos": {
            key: {
                "huella": mapa["modulos"][key]["huella"], "estado": estados[key],
                "hechos": len(ficha["hechos"]), "pendientes": len(ficha["pendientes"]),
            }
            for key, ficha in fichas.items()
        },
        "hechos": n_hechos, "pendientes": n_pendientes, "archivos_indexados": mapa["archivos_indexados"],
        "omisiones": mapa["omisiones"], "relaciones_pendientes": relaciones_pendientes,
    })
    resumen.update(
        operacion="publicar", commit=mapa["commit"], hechos=n_hechos, pendientes=n_pendientes,
        okf_version=VERSION_OKF, relaciones_pendientes=len(relaciones_pendientes),
        modulos_reutilizados=sum(value == "reutilizado" for value in estados.values()),
        modulos_sin_revision=sum(value == "pendiente" for value in estados.values()),
        caracteres_fuente=mapa["caracteres_fuente"],
        caracteres_corpus=sum(len(path.read_text(encoding="utf-8")) for path in corpus.rglob("*.md")),
    )
    print(f"OKF {VERSION_OKF} · {n_hechos} conceptos de QA · {n_pendientes} pendientes · corpus/")
    return 0 if n_hechos and not n_pendientes else 3


if __name__ == "__main__":
    principal(__file__, opciones, operar)
