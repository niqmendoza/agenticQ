"""Construir la distribución autocontenida de V9 para QA."""

import zipfile
from stat import S_IFREG
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
        "ejemplos/mockup.demo.json",
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
    v9 = RAIZ / "v9"
    archivos = [
        v9 / nombre
        for nombre in (".gitignore", "README.md", "INVENTARIO-SCRIPTS.md", "MEJORAS-V9.md", "requirements.txt", "credenciales.ejemplo.txt")
    ]
    for etapa, componentes in ETAPAS.items():
        archivos.extend(
            v9 / etapa / nombre
            for nombre in (*componentes, "PROMPT.md", "logs/.gitkeep")
        )
    for directorio in (
        "scripts", "01-analisis/scripts", "01-analisis/scripts/ragflow",
        "02-casos/scripts", "03-ejecuciones/scripts", "03-ejecuciones/scripts/benchmark",
    ):
        archivos.extend((v9 / directorio).glob("*.py"))
    destino = v9 / "Agentic-QC-V9.zip"
    with TemporaryDirectory(dir=v9) as tmp:
        copia = Path(tmp) / destino.name
        with zipfile.ZipFile(copia, "w", compression=zipfile.ZIP_DEFLATED) as paquete:
            for archivo in sorted(archivos):
                if not archivo.is_file() or archivo.is_symlink() or not archivo.resolve().is_relative_to(v9):
                    raise ValueError(f"Archivo de distribución inválido: {archivo}")
                paquete.write(archivo, archivo.relative_to(RAIZ))
            entrada = zipfile.ZipInfo("v9/credenciales.txt")
            entrada.create_system = 3
            entrada.external_attr = (S_IFREG | 0o600) << 16
            paquete.writestr(entrada, (v9 / "credenciales.ejemplo.txt").read_bytes())
        with zipfile.ZipFile(copia) as paquete:
            if paquete.testzip() is not None:
                raise ValueError("Falló la verificación del ZIP.")
        copia.replace(destino)
    return destino


if __name__ == "__main__":
    print(empaquetar())
