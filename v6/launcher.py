"""Puntos de entrada del paquete instalado."""

import os
import subprocess
import sys
from pathlib import Path


def launch(script):
    env = {**os.environ}
    env.setdefault("QC_WORKSPACE", str(Path.cwd() / ".agentic-qc"))
    return subprocess.call(
        [sys.executable, str(Path(__file__).parent / script), *sys.argv[1:]], env=env
    )


def main():
    return launch("src/qa.py")


def benchmark():
    return launch("evaluate-llm/evaluate.py")
