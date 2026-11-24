"""Ubicaciones del motor autocontenido de V8, independientes del directorio actual."""
import sys
from pathlib import Path

V8 = Path(__file__).resolve().parents[1]
ANALISIS = V8 / "01-analisis" / "scripts"
CASOS = V8 / "02-casos" / "scripts"
EJECUCIONES = V8 / "03-ejecuciones" / "scripts"


def cargar_motor():
    for directorio in (ANALISIS, CASOS, EJECUCIONES):
        if str(directorio) not in sys.path:
            sys.path.insert(0, str(directorio))
