"""Entregar un escenario de QC y, bajo presupuesto, sus rangos exactos de evidencia."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from soporte import abrir, principal, read_json, write_json

from fichas import comprobar_fuente
from indice import abrir_indice
from navegar import tamano
from perfil_qc import id_qc
from qc import ruta_qc


def cargar(cerebro):
    abrir(cerebro, "00-creacion-segundo-cerebro", requiere="fichas-qc.json")
    return read_json(cerebro / "manifiesto.json"), read_json(cerebro / "fichas-qc.json")


def extraer_caso(corpus, flujo, caso):
    path = ruta_qc(flujo)
    lines = (corpus / path).read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(f"## Caso {caso}")
    except ValueError:
        raise ValueError(f"El escenario {flujo}/{caso} no aparece en su ficha Markdown.") from None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## Caso ")), len(lines))
    return {"ruta": path, "desde": start + 1, "hasta": end, "texto": "\n".join(lines[start:end]).rstrip()}


def fragmentos_evidencia(case, db, cache):
    for ref in case["evidencia"]:
        cite = comprobar_fuente(ref, db, cache)
        if cite["blob"] != ref["blob"]:
            raise ValueError(f"La evidencia cambió desde la publicación: {cite['archivo']}.")
        yield {
            **ref,
            "texto": "\n".join(cache[cite["archivo"]][1][cite["desde"] - 1:cite["hasta"]]),
        }


def opciones(parser):
    parser.add_argument("--cerebro", type=Path, required=True)
    parser.add_argument("--mapa", type=Path)
    parser.add_argument("--flujo", required=True)
    parser.add_argument("--caso", required=True)
    parser.add_argument("--max-chars", type=int)


def operar(args, salida, logs, resumen):
    """Leer la ficha seleccionada. Con --mapa incluir únicamente su evidencia."""
    brain, flows = cargar(args.cerebro)
    flow = id_qc(args.flujo, "flujo")
    caseid = id_qc(args.caso, "caso")
    metadata = flows.get(flow, {})
    case = next((item for item in metadata.get("escenarios", []) if item["id"] == caseid), None)
    if case is None:
        raise ValueError("El escenario solicitado no está publicado.")
    profile = read_json(args.cerebro / "perfil-qc.json")
    maximum = profile["presupuesto"]["recuperacion_caracteres"]
    budget = args.max_chars if args.max_chars is not None else maximum
    if not 800 <= budget <= maximum:
        raise ValueError(f"Usá un presupuesto entre 800 y {maximum} caracteres.")
    result = {
        "flujo": flow, "caso": caseid, "revision": metadata["revision"],
        "ejecucion": case["ejecucion"]["estado"],
        "ficha": extraer_caso(args.cerebro / "corpus", flow, caseid),
        "evidencia": [], "referencias_esperadas": len(case["evidencia"]), "evidencia_recortada": False,
    }
    if tamano(result) > budget:
        raise ValueError("La ficha seleccionada supera el presupuesto. Acotá el escenario o ampliá el presupuesto.")
    if args.mapa:
        abrir(args.mapa, "00-creacion-segundo-cerebro", requiere="indice.sqlite")
        cache = {}
        with abrir_indice(args.mapa) as (mapa, db):
            if mapa["commit"] != brain["commit"]:
                raise ValueError("El mapa de evidencia debe ser del commit publicado.")
            for item in fragmentos_evidencia(case, db, cache):
                result["evidencia"].append(item)
                if tamano(result) > budget:
                    result["evidencia"].pop()
                    result["evidencia_recortada"] = True
    write_json(salida / "contexto-qc.json", result)
    resumen.update(operacion="recuperar-qc", commit=brain["commit"], flujo=flow, caso=caseid,
                   caracteres_contexto=tamano(result), contexto_recortado=result["evidencia_recortada"])
    return 3 if result["evidencia_recortada"] else 0


if __name__ == "__main__":
    principal(__file__, opciones, operar)
