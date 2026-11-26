"""Contrato único del CSV de QA usado para importar en Azure Test Plans."""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rutas import cargar_motor

cargar_motor()

from azure_export import cell

# Cada par conserva la columna visible y la clave de su valor. El orden define el CSV.
COLUMNAS = (
    ("ID", "id"),
    ("Tipo de elemento de trabajo", "work_item_type"),
    ("Título", "titulo"),
    ("Ruta de área", "area"),
    ("Asignado a", "assigned_to"),
    ("Estado", "state"),
    ("Tipo de caso de prueba", "test_case_type"),
    ("Funcionalidad", "functionality"),
    ("Tipo de componente", "component_type"),
    ("Tipo", "type"),
    ("Paso", "paso"),
    ("Acción", "accion"),
    ("Resultado esperado", "esperado"),
)
VALORES = {"work_item_type": "test case", "assigned_to": "", "state": "Design", "type": "Functional"}
CODIFICACION = "utf-8-sig"
LIMITE_TITULO = 128


def filas(casos, area):
    if not isinstance(area, str) or not area.strip():
        raise ValueError("Indicá la Ruta de área de Azure.")
    titulos, ids = set(), set()
    for caso in casos:
        meta = caso["azure"]
        titulo = caso["title"].strip()
        if not titulo or titulo.casefold() in titulos or len(titulo) > LIMITE_TITULO:
            raise ValueError(f"Título de Azure inválido o duplicado en {caso['id']}.")
        titulos.add(titulo.casefold())
        identificador = meta.get("work_item_id", "")
        if identificador != "":
            if type(identificador) is not int or identificador < 1 or identificador in ids:
                raise ValueError(f"ID de Azure inválido o duplicado en {caso['id']}.")
            ids.add(identificador)

        pares = list(zip(caso["steps"], caso["step_expected"], strict=True))
        if caso["preconditions"]:
            texto = "\n".join(f"- {linea}" for linea in caso["preconditions"])
            pares.insert(0, ("Precondiciones:\n" + texto, ""))
        fijos = {
            **VALORES,
            **{k: meta[k] for k in ("assigned_to", "state", "type") if k in meta},
            "id": identificador,
            "titulo": titulo,
            "area": meta.get("area", area),
            "test_case_type": meta["test_case_type"],
            "functionality": meta.get("functionality", caso["feature"]),
            "component_type": meta["component_type"],
        }
        for numero, (accion, esperado) in enumerate(pares, 1):
            valores = {**fijos, "paso": numero, "accion": accion, "esperado": esperado}
            yield [cell(valores[k]) for _, k in COLUMNAS]


def exportar(casos, area, ruta):
    registros = list(filas(casos, area))
    with Path(ruta).open("x", encoding=CODIFICACION, newline="") as stream:
        writer = csv.writer(stream, delimiter=",", lineterminator="\r\n")
        writer.writerow([titulo for titulo, _ in COLUMNAS])
        writer.writerows(registros)
    return len(registros)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--casos", required=True, type=Path)
    parser.add_argument("--area-qa", required=True)
    parser.add_argument("--salida", required=True, type=Path)
    args = parser.parse_args()
    try:
        casos = json.loads(args.casos.read_text(encoding="utf-8-sig"))
        exportar(casos, args.area_qa, args.salida)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"{error}\n")
    print(args.salida)


if __name__ == "__main__":
    main()
