"""Verifica recuperación y ejecución con una aplicación sintética, sin modelos externos."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRAIN = ROOT / 'Post Harness V2' / 'scripts' / 'brain.py'
RUNNER = ROOT / 'scripts' / 'run_tests.py'
EXAMPLE = ROOT / 'scripts' / 'ejemplo'


class FlujoE2E(unittest.TestCase):
    def test_recupera_y_ejecuta_y_registra_falla(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            app = work / 'app'
            shutil.copytree(EXAMPLE / 'aplicacion', app, ignore=shutil.ignore_patterns('__pycache__'))
            questions = work / 'preguntas.json'
            questions.write_text(json.dumps(['sumar cero valor']), encoding='utf-8')
            db = work / 'indice.sqlite'
            subprocess.run([sys.executable, str(BRAIN), '--db', str(db), 'index', str(EXAMPLE / 'segundo-cerebro')], check=True, capture_output=True)
            result = subprocess.run([sys.executable, str(BRAIN), '--db', str(db), '--session', str(work / 'sesion.json'), 'pack', '--queries-json', str(questions)], check=True, capture_output=True, text=True)
            context = json.loads(result.stdout)
            self.assertIn('cero', json.dumps(context, ensure_ascii=False).lower())
            self.assertTrue(context['sources'])
            for output, expected_status, expected_code in [('correcto', 'comando_exitoso', 0), ('defecto', 'comando_fallido', 1)]:
                if output == 'defecto':
                    (app / 'calculadora.py').write_text('def sumar(a, b):\n    return a - b\n', encoding='utf-8')
                target = work / output
                run = subprocess.run([sys.executable, str(RUNNER), '--cwd', str(app), '--out', str(target), '--', sys.executable, '-m', 'unittest', '-v', 'test_calculadora'], capture_output=True)
                self.assertEqual(run.returncode, expected_code)
                self.assertEqual(json.loads((target / 'resultado.json').read_text())['status'], expected_status)
                log = (target / 'stderr.txt').read_text()
                self.assertIn('Ran 2 tests', log)
                self.assertIn('FAIL' if output == 'defecto' else 'OK', log)
