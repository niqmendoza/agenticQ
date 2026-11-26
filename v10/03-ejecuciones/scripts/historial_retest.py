"""Relacionar dos entregas inmutables y adjuntar decisiones manuales por separado."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from consolidar import consolidar
from higiene import sanear
from soporte import abrir, huella, read_json, run_id


def snapshot(path):
    receipt = abrir(path, "03-ejecuciones", requiere="dictamen.json")
    info = read_json(path / "dictamen.json")
    engine_path = path / "resultados" / "resultado.json"
    engine = read_json(engine_path) if engine_path.is_file() else {}
    cases = {row["case"]: row for row in info.get("casos", [])}
    for key in info.get("casos_sin_ejecutar", []):
        cases.setdefault(key, {"status": "unattempted", "attempts": 0, "evidence": None, "first": "unattempted"})
    return {
        "id": run_id(receipt["id"]), "app": info["app"], "entorno": info["entorno"],
        "build": info["build"], "build_ref": info.get("build_ref"),
        "diseno_sha256": info["diseno_sha256"], "entrega_sha256": huella(path / "entrega.json"),
        "procedencia": engine.get("provenance", {}),
    }, cases


def evidencia_automatica(row, file_id):
    if row is None:
        return None
    return {
        "estado": row["status"], "primer_estado": row["first"], "intentos": row["attempts"],
        "evidencia": {"entrega": file_id, "ruta": row["evidence"]} if row["evidence"] else None,
    }


def comparar(base, actual, disposiciones):
    anterior, filas_antes = snapshot(base)
    nuevo, filas_despues = snapshot(actual)
    if any(anterior[campo] != nuevo[campo] for campo in ("app", "entorno")):
        raise ValueError("El retest requiere la misma aplicación y entorno.")
    if anterior["id"] == nuevo["id"]:
        raise ValueError("El retest requiere dos corridas con IDs distintos.")
    entradas_antes = anterior["procedencia"].get("inputs", {})
    entradas_despues = nuevo["procedencia"].get("inputs", {})
    decisiones = {}
    if not isinstance(disposiciones, dict) or disposiciones.keys() - filas_despues.keys():
        raise ValueError("Las decisiones deben referir a casos de la corrida actual.")
    for key, decision in disposiciones.items():
        if (
            not isinstance(decision, dict)
            or set(decision) != {"decision", "responsable", "motivo", "evidencia"}
            or decision["decision"] not in ("aceptado", "rechazado", "requiere_revision")
            or not all(isinstance(value, str) and value.strip() for value in decision.values())
        ):
            raise ValueError("Cada decisión requiere decisión válida, responsable, motivo y evidencia.")
        decisiones[key] = {name: sanear(value)[0] for name, value in decision.items()}
    profile_antes = anterior["procedencia"].get("profile")
    profile_despues = nuevo["procedencia"].get("profile")
    mismo_perfil = profile_antes == profile_despues if profile_antes and profile_despues else None
    rows = {}
    for key in sorted(filas_antes.keys() | filas_despues.keys()):
        row1, row2 = filas_antes.get(key), filas_despues.get(key)
        same = entradas_antes[key] == entradas_despues[key] if key in entradas_antes and key in entradas_despues else None
        rows[key] = {
            "anterior_automatico": evidencia_automatica(row1, anterior["id"]),
            "actual_automatico": evidencia_automatica(row2, nuevo["id"]),
            "mismos_criterios_y_entradas": same,
            "ejecutado_en_retest": bool(row2 and row2["attempts"]),
            "decision_manual": decisiones.get(key),
        }
    return {
        "schema": "agentic-qc/retest-1",
        "anterior": anterior, "actual": nuevo, "mismo_perfil": mismo_perfil, "casos": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anterior", required=True, type=Path)
    parser.add_argument("--actual", required=True, type=Path)
    parser.add_argument("--disposicion", type=Path)
    args = parser.parse_args()
    try:
        report = comparar(
            args.anterior.resolve(), args.actual.resolve(),
            read_json(args.disposicion) if args.disposicion else {},
        )
        etapa = Path(__file__).resolve().parents[1]
        current = report["actual"]["id"]
        folder = etapa / "logs" / current
        folder.mkdir(parents=True, exist_ok=True)
        sequence = 1
        while True:
            output = folder / f"historial-retest-{sequence:03}.json"
            try:
                with output.open("x", encoding="utf-8") as stream:
                    json.dump(report, stream, indent=2, ensure_ascii=False)
                    stream.write("\n")
                break
            except FileExistsError:
                sequence += 1
        consolidar(etapa, [current], individual=True)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, sanear(str(error))[0] + "\n")
    print(output)


if __name__ == "__main__":
    main()
