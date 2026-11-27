"""Publicar un segundo cerebro estándar con citas verificadas y módulos reutilizables."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from soporte import abrir, principal, read_json, write_json

from fichas import reusar, validar
from indice import abrir_indice
from okf import VERSION_OKF, publicar_okf
from qc import inventario_migracion, preparar_fichas, publicar_qc
from repositorio import SCHEMA
from tematico import planificar, publicar_tematico


def opciones(parser):
    parser.add_argument("--mapa", required=True, type=Path)
    parser.add_argument("--revision", action="append", type=Path, default=[], help="Ficha revisada. Se puede repetir.")
    parser.add_argument("--anterior", type=Path, help="Entrega de un segundo cerebro previo de la misma aplicación.")
    parser.add_argument("--fichas-qc", type=Path, action="append", default=[], help="Flujos y escenarios QC para el perfil V3.")
    parser.add_argument("--migracion", type=Path, help="Inventario de notas previas y sus decisiones.")
    formato = parser.add_mutually_exclusive_group(required=True)
    formato.add_argument("--taxonomia", type=Path, help="Plan de áreas de producto y mapas de contenido.")
    formato.add_argument("--por-modulo", action="store_true", help="Reconstruir expresamente una entrega anterior.")


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
        perfil = mapa.get("perfil_qc")
        if (args.fichas_qc or args.migracion) and not perfil:
            raise ValueError("Las fichas QC y la migración requieren un mapa creado con --perfil.")
        if perfil and not args.taxonomia:
            raise ValueError("El perfil V3 requiere publicación temática con --taxonomia.")
        flujos = preparar_fichas(args.fichas_qc, args.anterior, mapa, fichas, db, cache) if perfil else {}
    corpus = salida / "corpus"
    grafo = {"organizacion": "modulos"}
    if args.taxonomia:
        try:
            taxonomia, rutas, notas, salientes, entrantes, errores = planificar(read_json(args.taxonomia), fichas)
        except ValueError as error:
            write_json(logs / "validacion-grafo.json", {"incidencias": [{"causa": "taxonomia_invalida"}]})
            raise ValueError(f"Taxonomía inválida. {error}") from None
        write_json(logs / "validacion-grafo.json", {"incidencias": errores, "conceptos": len(notas)})
        if errores:
            raise ValueError(f"El grafo tiene {len(errores)} incidencias. Revisá validacion-grafo.json.")
        publicar_tematico(corpus, mapa, taxonomia, rutas, notas, salientes, entrantes)
        write_json(salida / "taxonomia.json", taxonomia)
        relaciones_pendientes = []
        grafo = {
            "organizacion": "tematica", "areas": len(taxonomia["areas"]), "mocs": len(taxonomia["mocs"]),
            "relaciones_justificadas": sum(map(len, salientes.values())),
        }
    else:
        relaciones_pendientes = publicar_okf(corpus, mapa, fichas)
    qc = {}
    if perfil:
        cobertura = publicar_qc(corpus, mapa, flujos, rutas)
        write_json(salida / "fichas-qc.json", flujos)
        write_json(salida / "perfil-qc.json", perfil)
        if args.migracion:
            write_json(salida / "migracion.json", inventario_migracion(args.migracion, flujos))
        qc = {"version": 3, "entrada": "inicio.md", "flujos_criticos": cobertura}
    n_hechos = sum(len(ficha["hechos"]) for ficha in fichas.values())
    n_pendientes = sum(len(ficha["pendientes"]) for ficha in fichas.values()) + len(relaciones_pendientes)
    n_pendientes += sum(row["estado"] != "listo-para-qc" for row in qc.get("flujos_criticos", {}).values())
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
        "grafo": grafo,
        **({"qc": qc} if perfil else {}),
    })
    resumen.update(
        operacion="publicar", commit=mapa["commit"], hechos=n_hechos, pendientes=n_pendientes,
        okf_version=VERSION_OKF, relaciones_pendientes=len(relaciones_pendientes),
        **grafo,
        modulos_reutilizados=sum(value == "reutilizado" for value in estados.values()),
        modulos_sin_revision=sum(value == "pendiente" for value in estados.values()),
        caracteres_fuente=mapa["caracteres_fuente"],
        caracteres_corpus=sum(len(path.read_text(encoding="utf-8")) for path in corpus.rglob("*.md")),
    )
    print(f"OKF {VERSION_OKF} · {n_hechos} conceptos de QA · {n_pendientes} pendientes · corpus/")
    return 0 if n_hechos and not n_pendientes else 3


if __name__ == "__main__":
    principal(__file__, opciones, operar)
