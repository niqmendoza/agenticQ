"""Copiar el corpus publicado a una bóveda nueva y enlazar guías preexistentes."""

import argparse
import os
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from soporte import abrir

from fichas import texto
from okf import linea_enlace


def exportar(cerebro, destino, referencias):
    origen = cerebro.resolve()
    abrir(origen, "00-creacion-segundo-cerebro", requiere="corpus/index.md")
    dest = destino.parent.resolve() / destino.name
    if dest.exists() or dest.is_symlink() or dest.is_relative_to(origen):
        raise ValueError("Elegí una carpeta nueva fuera de la entrega original.")

    enlaces = []
    for titulo, ruta in referencias:
        fuente = Path(ruta).resolve(strict=True)
        if fuente.suffix.casefold() != ".md" or not fuente.is_file():
            raise ValueError("Cada referencia preexistente debe apuntar a un archivo Markdown.")
        try:
            href = quote(Path(os.path.relpath(fuente, dest)).as_posix(), safe="/")
        except ValueError:
            href = fuente.as_uri()
        enlaces.append(linea_enlace(texto(titulo, 100, "titulo"), href, "Referencia preexistente."))

    dest.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=dest.parent) as tmp:
        staging = Path(tmp) / "corpus"
        shutil.copytree(origen / "corpus", staging)
        if enlaces:
            with (staging / "index.md").open("a", encoding="utf-8") as index:
                index.write("\n## Notas preexistentes\n\n" + "\n".join(enlaces) + "\n")
        dest.mkdir()  # Reserva exclusiva: falla si otro proceso creó el destino.
        try:
            for child in staging.iterdir():
                child.rename(dest / child.name)
        except OSError:
            shutil.rmtree(dest)
            raise
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cerebro", required=True, type=Path)
    parser.add_argument("--destino", required=True, type=Path)
    parser.add_argument("--referencia", nargs=2, action="append", default=[], metavar=("TITULO", "ARCHIVO"))
    args = parser.parse_args()
    try:
        print(exportar(args.cerebro, args.destino, args.referencia))
    except (ValueError, OSError) as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    main()
