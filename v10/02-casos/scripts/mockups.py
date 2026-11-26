"""Generar fixtures reproducibles de QA sin datos ni credenciales del entorno."""

import csv
import json
import sys
from html import escape
from pathlib import Path
from random import Random
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from soporte import huella, principal, read_json, run_id, write_json

from formatos_fixture import inspeccionar, pdf, xlsx
from mock_data import mock_values

FORMATOS = ("json", "csv", "txt", "md", "html", "docx", "xlsx", "pdf")
WORD = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def opciones(parser):
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--nombre", required=True, type=run_id)
    parser.add_argument("--formato", required=True, choices=FORMATOS)
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--cantidad", type=int, default=1)


def escribir_docx(archivo, lineas):
    parrafos = "".join(
        f'<w:p><w:r><w:t xml:space="preserve">{escape(linea)}</w:t></w:r></w:p>'
        for linea in lineas
    )
    with ZipFile(archivo, "w", compression=ZIP_DEFLATED) as paquete:
        archivos = {
            "[Content_Types].xml": (
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                '</Types>'
            ),
            "_rels/.rels": (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                '</Relationships>'
            ),
            "word/document.xml": f'<w:document xmlns:w="{WORD}"><w:body>{parrafos}<w:sectPr/></w:body></w:document>',
        }
        for nombre, contenido in archivos.items():
            # Fecha fija para reproducibilidad binaria.
            paquete.writestr(ZipInfo(nombre), contenido, compress_type=ZIP_DEFLATED)


def renderizar(archivo, formato, filas):
    if formato == "json":
        write_json(archivo, filas[0] if len(filas) == 1 else filas)
        return
    if formato == "xlsx":
        xlsx(archivo, list(filas[0]), [list(fila.values()) for fila in filas])
        return
    if formato == "csv":
        with archivo.open("w", newline="", encoding="utf-8-sig") as salida:
            writer = csv.DictWriter(salida, fieldnames=filas[0].keys())
            writer.writeheader()
            writer.writerows(filas)
        return
    lineas = ["Datos sintéticos de QA"]
    for i, fila in enumerate(filas, 1):
        lineas.extend(
            [f"Registro {i}"] + [
                f"{clave}: {valor if isinstance(valor, str) else json.dumps(valor, ensure_ascii=False)}"
                for clave, valor in fila.items()
            ]
        )
    if formato == "pdf":
        pdf(archivo, lineas)
    elif formato == "docx":
        escribir_docx(archivo, lineas)
    elif formato == "html":
        texto = "\n".join(f"<p>{escape(linea)}</p>" for linea in lineas)
        archivo.write_text(
            '<!doctype html>\n<html lang="es"><meta charset="utf-8"><title>Fixture de QA</title>'
            f"<body>{texto}</body></html>\n", encoding="utf-8",
        )
    else:
        if formato == "md":
            lineas[0] = "# " + lineas[0]
        archivo.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def operar(args, salida, logs, resumen):
    """Crear datos de prueba portables para vincular desde el diseño."""
    if not 1 <= args.cantidad <= 1000:
        raise ValueError("La cantidad de registros debe estar entre 1 y 1000.")
    generadores = mock_values(read_json(args.spec), Random(args.semilla))
    filas = [
        {nombre: generar(i) for nombre, generar in generadores.items()}
        for i in range(1, args.cantidad + 1)
    ]
    fixtures = salida / "fixtures"
    fixtures.mkdir()
    archivo = fixtures / f"{args.nombre}.{args.formato}"
    renderizar(archivo, args.formato, filas)
    estructura = inspeccionar(archivo)
    if args.formato == "xlsx" and estructura["filas_datos"] != args.cantidad:
        raise ValueError("El XLSX no contiene la cantidad de registros solicitada.")
    if args.formato == "pdf" and not estructura["paginas"]:
        raise ValueError("El PDF no contiene páginas.")
    registro = {
        "generador": "v10/mockups-1",
        "estructura": estructura,
        "spec_sha256": huella(args.spec),
        "fixture": archivo.relative_to(salida).as_posix(),
        "fixture_sha256": huella(archivo),
        "bytes": archivo.stat().st_size,
        "formato": args.formato,
        "semilla": args.semilla,
        "cantidad": args.cantidad,
    }
    write_json(salida / "mockup.json", registro)
    resumen.update(registro)
    return 0


if __name__ == "__main__":
    principal(__file__, opciones, operar)
