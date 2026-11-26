"""Recuperar fragmentos de documentación funcional aportada al diseñar casos."""

import sys
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from higiene import sanear
from soporte import abrir, huella, paquete_documental, principal, read_json, write_json


def opciones(parser):
    parser.add_argument("--analisis", required=True, type=Path)
    parser.add_argument(
        "--documento-funcional", required=True, action="append", type=Path
    )
    parser.add_argument(
        "--consulta",
        action="append",
        help="Búsqueda más específica para esta iteración",
    )
    parser.add_argument("--max-chars", type=int, default=12000)


def leer_documento(path):
    nombre = path.name.casefold()
    if nombre == "credenciales.txt" or nombre == ".env" or nombre.startswith(".env."):
        raise ValueError("Ingresá un documento funcional. Las credenciales se cargan en ejecución.")
    extension = path.suffix.casefold()
    if extension in {".md", ".markdown", ".txt", ".rst"}:
        return path.read_text(encoding="utf-8-sig")
    if extension == ".docx":
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        try:
            with ZipFile(path) as archivo:
                raiz = ElementTree.fromstring(archivo.read("word/document.xml"))
        except (BadZipFile, ElementTree.ParseError) as exc:
            raise ValueError(f"Documento Word inválido: {path.name}") from exc
        return "\n".join(
            "".join(t.text or "" for t in p.iter(ns + "t")) for p in raiz.iter(ns + "p")
        )
    if extension == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError(
                "Para extraer texto de PDF instalá pypdf en este intérprete."
            ) from None
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    raise ValueError(f"Formato de documentación funcional no admitido: {extension}")


def operar(args, salida, logs, resumen):
    """Preparar un contexto opcional y acotado para el segundo prompt."""
    abrir(args.analisis, "01-analisis", requiere="reglas.json")
    encargo = read_json(args.analisis / "encargo.json")
    reglas = read_json(args.analisis / "reglas.json")
    consultas = args.consulta or list(
        dict.fromkeys(r["objetivo"] for r in encargo["recorridos"])
    )
    if args.max_chars < 3000 or len(consultas) > 20:
        raise ValueError(
            "Usá al menos 3000 caracteres y hasta 20 consultas, agrupadas por tarea."
        )
    documentos = {}
    segmentos = {}
    with TemporaryDirectory() as temporal:
        corpus = Path(temporal)
        for numero, path in enumerate(args.documento_funcional, 1):
            if path.name in documentos:
                raise ValueError(
                    f"Se necesitan nombres de documento distintos: {path.name}"
                )
            texto, redacciones = sanear(leer_documento(path))
            if not texto.strip():
                raise ValueError(
                    f"{path.name}: sin texto extraíble. Proporcioná una transcripción."
                )
            lineas = texto.splitlines()
            h = huella(path)
            documentos[path.name] = {"sha256": h, "lineas_extraidas": len(lineas), "redacciones": redacciones}
            # Las unidades pequeñas permiten recuperar una regla al final de un manual extenso.
            for i in range(0, len(lineas), 20):
                nombre = f"{numero}-{i + 1}.txt"
                (corpus / nombre).write_text(
                    "\n".join(lineas[i : i + 20]), encoding="utf-8"
                )
                segmentos[nombre] = (path.name, i, h)
        datos = paquete_documental(corpus, consultas, args.max_chars, logs)
    fuentes = salida / "fuentes"
    fuentes.mkdir()
    extractos = []
    for p in datos["passages"]:
        clave = datos["sources"][p["source"]]["path"]
        original, desplazamiento, h = segmentos[clave]
        inicio, fin = desplazamiento + p["start"], desplazamiento + p["end"]
        nombre = f"F-{sha256(original.encode()).hexdigest()[:12]}-{inicio}-{fin}.txt"
        texto = "\n".join(linea.partition("|")[2] for linea in p["text"].split("\n"))
        (fuentes / nombre).write_text(texto + "\n", encoding="utf-8")
        extractos.append(
            {
                "archivo": nombre,
                "original": original,
                "sha256_original": h,
                "desde": inicio,
                "hasta": fin,
                "origen": "funcional",
            }
        )
    originales_analisis = {
        e["sha256_original"] for e in read_json(args.analisis / "analisis.json")["extractos"]
    }
    contexto = {
        "analisis_sha256": huella(args.analisis / "entrega.json"),
        "documentos": {
            nombre: {**doc, "tambien_en_segundo_cerebro": doc["sha256"] in originales_analisis}
            for nombre, doc in documentos.items()
        },
        "consultas": datos["queries"],
        "extractos": extractos,
    }
    write_json(salida / "documentacion-funcional.json", contexto)
    resumen.update(
        operacion="consulta funcional",
        documentos=documentos,
        extractos=len(extractos),
        presupuesto_caracteres=args.max_chars,
        recorridos=list(reglas),
    )
    return 0 if extractos else 3


if __name__ == "__main__":
    principal(__file__, opciones, operar)
