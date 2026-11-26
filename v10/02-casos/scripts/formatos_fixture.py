"""Generar y comprobar XLSX y PDF pequeños, sin depender de una suite de oficina."""

from html import escape
from xml.etree import ElementTree as XML
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

HOJA = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"


def xlsx(path, headers, rows):
    def celda(valor):
        if type(valor) is bool:
            return f'<c t="b"><v>{int(valor)}</v></c>'
        if type(valor) in (int, float):
            return f'<c><v>{valor}</v></c>'
        if valor is None:
            return "<c/>"
        return f'<c t="inlineStr"><is><t xml:space="preserve">{escape(str(valor))}</t></is></c>'

    tabla = "".join(
        "<row>" + "".join(celda(v) for v in fila) + "</row>"
        for fila in (headers, *rows)
    )
    partes = {
        "[Content_Types].xml":
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        "_rels/.rels":
            f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" Type="{DOC}/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml":
            f'<workbook xmlns="{HOJA}" xmlns:r="{DOC}"><sheets><sheet name="QA" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels":
            f'<Relationships xmlns="{PKG}"><Relationship Id="rId1" Type="{DOC}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": f'<worksheet xmlns="{HOJA}"><sheetData>{tabla}</sheetData></worksheet>',
    }
    with ZipFile(path, "w") as z:
        for nombre, contenido in partes.items():
            z.writestr(ZipInfo(nombre), contenido, compress_type=ZIP_DEFLATED)


def pdf(path, lineas):
    # PDF de texto simple. Fuente estándar con codificación WinAnsi y paginación fija.
    def literal(linea):
        try:
            b = linea.encode("cp1252")
        except UnicodeEncodeError as error:
            raise ValueError("PDF sintético requiere texto representable en WinAnsi. Usá DOCX para Unicode completo.") from error
        return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")

    lineas = [l[i:i+95] for texto in lineas for l in texto.splitlines() for i in range(0, len(l) or 1, 95)]
    paginas = [lineas[i:i+54] for i in range(0, len(lineas), 54)]
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Count {len(paginas)} /Kids ["
        .encode() + b" ".join(f"{n} 0 R".encode() for n in range(4, 4+2*len(paginas), 2)) + b"] >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    for pagina in paginas:
        n = len(objetos) + 1
        objetos.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources "
            f"<< /Font << /F1 3 0 R >> >> /Contents {n+1} 0 R >>".encode()
        )
        cuerpo = b"BT /F1 11 Tf 13 TL 42 797 Td\n" + b"\n".join(
            b"(" + literal(l) + b") Tj T*" for l in pagina
        ) + b"\nET\n"
        objetos.append(f"<< /Length {len(cuerpo)} >>\nstream\n".encode() + cuerpo + b"endstream")
    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for n, obj in enumerate(objetos, 1):
        offsets.append(len(data))
        data.extend(f"{n} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objetos)+1}\n0000000000 65535 f \n".encode())
    for inicio in offsets:
        data.extend(f"{inicio:010} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(objetos)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(data)
    return {"paginas": len(paginas)}


def leer_xml(path, nombre):
    with ZipFile(path) as z:
        if z.getinfo(nombre).file_size > 8 * 1024 * 1024:
            raise ValueError("El XML del archivo supera el límite de lectura.")
        return XML.fromstring(z.read(nombre))


def inspeccionar(path):
    """Confirmar que el archivo generado contiene partes estructurales y filas esperadas."""
    extension = path.suffix.casefold()
    if extension == ".xlsx":
        libro = leer_xml(path, "xl/workbook.xml")
        hoja = leer_xml(path, "xl/worksheets/sheet1.xml")
        filas = list(hoja.iter(f"{{{HOJA}}}row"))
        return {"hojas": len(list(libro.iter(f"{{{HOJA}}}sheet"))),
                "filas_datos": len(filas) - 1,
                "columnas": len(filas[0])}
    if extension == ".pdf":
        raw = path.read_bytes()
        if not raw.startswith(b"%PDF-") or not raw.rstrip().endswith(b"%%EOF"):
            raise ValueError("El PDF generado no tiene la estructura esperada.")
        return {"paginas": raw.count(b"/Type /Page /Parent")}
    if extension == ".docx":
        leer_xml(path, "word/document.xml")
    return {}
