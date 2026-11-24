"""Construir la distribución autocontenida de V8 para QA."""

import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
ETAPAS = {
    "01-analisis": (
        "ejemplos/encargo.demo.json",
        "ejemplos/revision.demo.json",
        "ejemplos/corpus/reglas.md",
    ),
    "02-casos": (
        "ejemplos/diseno.demo.json",
        "ejemplos/guia-funcional.demo.md",
    ),
    "03-ejecuciones": (
        "MEDICION-TOKENS.md",
        "requirements-postgres.txt",
        "plantillas/README.md",
        "plantillas/analisis.md",
        "plantillas/azure-test-cases.csv",
        "plantillas/evaluacion.md",
        "plantillas/metricas.md",
        "plantillas/reporte-gerencial.html",
        "plantillas/sdd-fix.md",
        "scripts/benchmark/README.md",
        "scripts/benchmark/INSTRUCCIONES.md",
        "scripts/benchmark/comparacion.html",
        "scripts/benchmark/benchmark.ejemplo.json",
        "scripts/benchmark/experimento.ejemplo.json",
        "scripts/benchmark/revision.ejemplo.json",
    ),
}


def empaquetar():
    v8 = RAIZ / "v8"
    archivos = [
        v8 / nombre
        for nombre in (".gitignore", "README.md", "INVENTARIO-SCRIPTS.md", "requirements.txt")
    ]
    for etapa, componentes in ETAPAS.items():
        archivos.extend(
            v8 / etapa / nombre
            for nombre in (*componentes, "PROMPT.md", "logs/.gitkeep")
        )
    for directorio in (
        "scripts", "01-analisis/scripts", "01-analisis/scripts/ragflow",
        "02-casos/scripts", "03-ejecuciones/scripts", "03-ejecuciones/scripts/benchmark",
    ):
        archivos.extend((v8 / directorio).glob("*.py"))
    destino = v8 / "Agentic-QC-V8.zip"
    with TemporaryDirectory(dir=v8) as tmp:
        copia = Path(tmp) / destino.name
        with zipfile.ZipFile(copia, "w", compression=zipfile.ZIP_DEFLATED) as paquete:
            for archivo in sorted(archivos):
                if not archivo.is_file() or archivo.is_symlink() or not archivo.resolve().is_relative_to(v8):
                    raise ValueError(f"Archivo de distribución inválido: {archivo}")
                paquete.write(archivo, archivo.relative_to(RAIZ))
        with zipfile.ZipFile(copia) as paquete:
            if paquete.testzip() is not None:
                raise ValueError("Falló la verificación del ZIP.")
        copia.replace(destino)
    return destino


if __name__ == "__main__":
    print(empaquetar())
