"""Ubicaciones del motor autocontenido de V10, independientes del directorio actual."""
import sys
from pathlib import Path

V10 = Path(__file__).resolve().parents[1]
ANALISIS = V10 / "01-analisis" / "scripts"
CASOS = V10 / "02-casos" / "scripts"
EJECUCIONES = V10 / "03-ejecuciones" / "scripts"


def cargar_motor():
    for directorio in (ANALISIS, CASOS, EJECUCIONES):
        if str(directorio) not in sys.path:
            sys.path.insert(0, str(directorio))
