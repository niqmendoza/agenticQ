import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / 'scripts' / 'empaquetar_evidencia.py'
RUN = ROOT / 'scripts' / 'run_tests.py'
VERIFY = ROOT / 'scripts' / 'verificar_evidencia.py'
TEMPLATE = ROOT / 'scripts' / 'ejemplo' / 'evidencia-ejemplo.json'


class PaqueteTest(unittest.TestCase):
    def test_ejecucion_sintetica_y_paquete_verificable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); base = root / 'seleccion'; base.mkdir()
            app = ROOT / 'scripts' / 'ejemplo' / 'aplicacion'
            execution = base / 'ejecucion'
            subprocess.run([sys.executable, str(RUN), '--cwd', str(app), '--out', str(execution), '--', sys.executable, '-B', '-m', 'unittest', '-v', 'test_calculadora'], check=True, capture_output=True)
            manifest = json.loads(TEMPLATE.read_text())
            manifest['cases'][0]['result'] = 'Dos pruebas sintéticas aprobadas; revisar log'
            manifest['cases'][0]['evidence'] = 'artefactos/001-resultado.json y artefactos/002-stderr.txt'
            manifest['artifacts'] = [{'path':'ejecucion/resultado.json', 'description':'Estado del comando'}, {'path':'ejecucion/stderr.txt', 'description':'Salida del test sintético'}]
            input_file = root / 'entrada.json'; input_file.write_text(json.dumps(manifest), encoding='utf-8')
            out = root / 'paquete'
            subprocess.run([sys.executable, str(PACK), '--manifest', str(input_file), '--base', str(base), '--out', str(out), '--reviewed'], check=True, capture_output=True)
            package = json.loads((out / 'evidencia.json').read_text())
            self.assertEqual(package['stages']['coelsa'], 'no_ejecutado')
            for item in package['artifacts']:
                self.assertEqual(hashlib.sha256((out / item['path']).read_bytes()).hexdigest(), item['sha256'])
            self.assertIn('Ran 2 tests', (out / package['artifacts'][1]['path']).read_text())
            self.assertIn('no_ejecutado', (out / 'RESUMEN.md').read_text())
            subprocess.run([sys.executable, str(VERIFY), str(out)], check=True, capture_output=True)
            (out / package['artifacts'][1]['path']).write_text('alterado', encoding='utf-8')
            self.assertNotEqual(subprocess.run([sys.executable, str(VERIFY), str(out)], capture_output=True).returncode, 0)
            self.assertNotEqual(subprocess.run([sys.executable, str(PACK), '--manifest', str(input_file), '--base', str(base), '--out', str(out), '--reviewed'], capture_output=True).returncode, 0)

    def test_rechaza_ruta_externa(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); base = root / 'seleccion'; base.mkdir()
            manifest = json.loads(TEMPLATE.read_text()); manifest['artifacts'] = [{'path':'../secreto', 'description':'no copiar'}]
            path = root / 'entrada.json'; path.write_text(json.dumps(manifest))
            out = root / 'paquete'
            proc = subprocess.run([sys.executable, str(PACK), '--manifest', str(path), '--base', str(base), '--out', str(out), '--reviewed'], capture_output=True)
            self.assertNotEqual(proc.returncode, 0); self.assertFalse(out.exists())
