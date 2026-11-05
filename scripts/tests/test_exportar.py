import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

EXPORT = Path(__file__).resolve().parents[1] / 'exportar.py'


class Exportar(unittest.TestCase):
    def test_pasos_y_csv_excel(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = {'schema': 'qa-regression/1', 'application': 'Ejemplo', 'cases': [{
                'id': 'C1', 'title': 'Texto, acentos', 'steps': ['Abrir, pantalla', '=acción'],
                'expected': 'Resultado\nobservable', 'feature': 'Función', 'tests': 'tests/test.py',
                'references': [{'source': 'D1', 'quote': 'regla'}], 'context_sha256': 'ejemplo', 'review': 'human_confirmed'}]}
            path = root / 'registro.json'; path.write_text(json.dumps(registry), encoding='utf-8')
            out = root / 'salida'
            subprocess.run([sys.executable, str(EXPORT), '--registry', str(path), '--out', str(out), '--area', 'Proyecto', '--assigned-to', 'qa@example.test', '--state', 'Design', '--release', 'R1'], check=True, capture_output=True)
            with (out / 'azure-test-cases.csv').open(encoding='utf-8-sig', newline='') as f: rows = list(csv.DictReader(f))
            self.assertEqual([r['Test Step'] for r in rows], ['1', '2'])
            self.assertEqual(rows[0]['Step Expected'], '')
            self.assertEqual(rows[1]['Step Expected'], 'Resultado\nobservable')
            self.assertEqual(rows[1]['Step Action'], "'=acción")
            with (out / 'registro-pruebas.csv').open(encoding='utf-8-sig', newline='') as f: table = list(csv.DictReader(f))
            self.assertEqual(table[0]['Resultado'], 'No informado')
            self.assertEqual(json.loads((out / 'trazabilidad.json').read_text())['cases'][0]['steps'][1], '=acción')
