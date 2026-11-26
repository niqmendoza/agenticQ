"""Consolidar los artefactos locales en Markdown sin duplicar copias idénticas."""

import hashlib
import json
from html import escape
import os
import re
from pathlib import Path
from tempfile import NamedTemporaryFile

from higiene import sanear
from metricas_etapa import publicar

TEXTO = {".csv": "csv", ".html": "html", ".json": "json", ".jsonl": "jsonl",
         ".log": "text", ".md": "markdown", ".rst": "text", ".txt": "text",
         ".xml": "xml", ".yaml": "yaml", ".yml": "yaml"}
NOMBRES = {
    "00-creacion-segundo-cerebro": "log00.md",
    "01-analisis": "log01.md", "02-casos": "log02.md", "03-ejecuciones": "log03.md",
}


def lista_archivos(etapa, ids):
    for identificador in dict.fromkeys(ids):
        for carpeta in ("salidas", "logs"):
            raiz = etapa / carpeta / identificador
            if raiz.is_symlink():
                continue
            for archivo in sorted(raiz.rglob("*")):
                if (archivo.is_file() and not archivo.is_symlink()
                    and not archivo.name.startswith(".")
                    and archivo.name not in NOMBRES.values()
                    and not re.search(r"credencial|\.env(?:\.|$)|\.(?:pem|key|p12)$", archivo.name, re.I)
                    and archivo.resolve().is_relative_to(raiz.resolve())):
                    yield archivo


def incluir(stream, ruta, relativo, vistos):
    if ruta.suffix.casefold() not in TEXTO:
        with ruta.open("rb") as archivo:
            hash_binario = hashlib.sha256()
            for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
                hash_binario.update(bloque)
        stream.write(f"- Binario. {ruta.stat().st_size} bytes. SHA-256 `{hash_binario.hexdigest()}`.\n")
        return
    try:
        texto = ruta.read_text(encoding="utf-8-sig")
    except UnicodeError:
        stream.write("- Texto con codificación distinta de UTF-8. Consultá el original.\n")
        return
    texto, redacciones = sanear(texto)
    if redacciones:
        stream.write(f"- Valores sensibles redactados: {redacciones}.\n\n")
    digest = hashlib.sha256(texto.encode()).digest()
    if digest in vistos:
        stream.write(f"- Mismo contenido que `{vistos[digest]}`, embebido en este log.\n")
        return
    vistos[digest] = relativo
    cierre = "`" * max(4, 1 + max((len(m[0]) for m in re.finditer(r"`+", texto)), default=0))
    stream.write(f"{cierre}{TEXTO[ruta.suffix.casefold()]}\n{texto}")
    if not texto.endswith("\n"):
        stream.write("\n")
    stream.write(f"{cierre}\n")


def mostrar_resumen(stream, etapa, ids):
    stream.write("\n## Resumen de ejecuciones\n\n")
    stream.write("| ID | Estado | Código | Tiempo del script | Resultado |\n")
    stream.write("|---|---|---:|---:|---|\n")
    for identificador in ids:
        raiz = etapa / "logs" / identificador
        if raiz.is_symlink():
            continue
        filas = []
        for resumen in raiz.glob("*/resumen.json"):
            if resumen.is_symlink() or not resumen.resolve().is_relative_to(raiz.resolve()):
                continue
            try:
                fila = json.loads(resumen.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            filas.append(fila)
        for fila in sorted(filas, key=lambda r: r.get("inicio_utc", "")):
            resultado = fila.get("dictamen") or fila.get("fase") or fila.get("operacion") or "Ver resumen del intento."
            celdas = (identificador, fila.get("estado", ""), fila.get("codigo", ""),
                      fila.get("duracion_segundos", ""), resultado)
            linea = " | ".join(escape(sanear(str(valor))[0]).replace("|", "&#124;").replace("\n", " ") for valor in celdas)
            stream.write(f"| {linea} |\n")


def consolidar(etapa, ids, *, individual=False):
    nombre = NOMBRES[etapa.name]
    destino = etapa / "logs" / ids[0] / nombre if individual else etapa / "logs" / nombre
    destino.parent.mkdir(parents=True, exist_ok=True)
    for identifier in dict.fromkeys(ids):
        publicar(etapa, identifier)
    vistos = {}
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=destino.parent, delete=False
    ) as stream:
        temporal = Path(stream.name)
        try:
            stream.write(f"# {nombre.removesuffix('.md')} · {etapa.name}\n\n")
            stream.write("IDs incluidos · " + ", ".join(f"`{i}`" for i in ids) + "\n")
            mostrar_resumen(stream, etapa, ids)
            for ruta in lista_archivos(etapa, ids):
                relativo = ruta.relative_to(etapa).as_posix()
                stream.write(f"\n## {relativo}\n\n")
                incluir(stream, ruta, relativo, vistos)
            stream.flush()
            os.replace(temporal, destino)
        finally:
            temporal.unlink(missing_ok=True)
    return destino
