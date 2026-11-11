"""Verifica recuperación y ejecución con una aplicación sintética, sin modelos externos."""
import json
import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRAIN = ROOT / 'historico' / 'Post Harness V2' / 'scripts' / 'brain.py'
RUNNER = ROOT / 'scripts' / 'run_tests.py'
VALIDATOR = ROOT / 'scripts' / 'validar_casos.py'
REGISTRY = ROOT / 'scripts' / 'regresion.py'
EXPORT = ROOT / 'scripts' / 'exportar.py'
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
            # Caso sintético escrito para el ensayo: no simula una llamada a Copilot.
            source = next(iter(context['sources']))
            cases = {'schema': 'qa-cases/1', 'cases': [{'id': 'C1', 'title': 'Suma con cero',
                     'steps': ['Sumar siete y cero'], 'expected': 'Devuelve siete',
                     'references': [{'source': source, 'quote': 'La suma de cero no cambia el valor recibido.'}]}]}
            context_file, cases_file = work / 'contexto.json', work / 'casos.json'
            context_file.write_text(json.dumps(context), encoding='utf-8')
            cases_file.write_text(json.dumps(cases), encoding='utf-8')
            validation = work / 'validacion.json'
            subprocess.run([sys.executable, str(VALIDATOR), '--context', str(context_file), '--cases', str(cases_file), '--out', str(validation)], check=True, capture_output=True)
            self.assertTrue(json.loads(validation.read_text())['valid'])
            registry = work / 'regresion.json'
            subprocess.run([sys.executable, str(REGISTRY), 'init', '--registry', str(registry), '--application', 'Ejemplo'], check=True, capture_output=True)
            add = [sys.executable, str(REGISTRY), 'add', '--registry', str(registry), '--context', str(context_file), '--cases', str(cases_file), '--feature', 'Suma', '--tests', 'test_calculadora.py', '--reviewed']
            subprocess.run(add, check=True, capture_output=True)
            self.assertNotEqual(subprocess.run(add, capture_output=True).returncode, 0)
            plan = work / 'release.json'
            subprocess.run([sys.executable, str(REGISTRY), 'plan', '--registry', str(registry), '--release', '2', '--feature', 'Nueva función', '--changed-rules', '--out', str(plan)], check=True, capture_output=True)
            release = json.loads(plan.read_text())
            self.assertEqual(release['regression_case_ids'], ['C1'])
            self.assertEqual(release['new_feature'], 'Nueva función')
            self.assertEqual(release['existing_rules_status'], 'revision_requerida')
            self.assertEqual(release['execution_status'], 'pendiente')
            new_cases = {'schema': 'qa-cases/1', 'cases': [{'id': 'C2', 'title': 'Suma de números', 'steps': ['Sumar dos y tres'], 'expected': 'Devuelve cinco', 'references': [{'source': source, 'quote': 'La función sumar recibe dos números y devuelve su suma.'}]}]}
            new_file = work / 'nuevos.json'
            new_file.write_text(json.dumps(new_cases), encoding='utf-8')
            subprocess.run([sys.executable, str(REGISTRY), 'add', '--registry', str(registry), '--context', str(context_file), '--cases', str(new_file), '--feature', 'Nueva función', '--tests', 'test_calculadora.py', '--reviewed'], check=True, capture_output=True)
            self.assertEqual([c['id'] for c in json.loads(registry.read_text())['cases']], ['C1', 'C2'])
            blank_plan = work / 'sin-funcion.json'
            subprocess.run([sys.executable, str(REGISTRY), 'plan', '--registry', str(registry), '--release', '3', '--out', str(blank_plan)], check=True, capture_output=True)
            self.assertEqual(json.loads(blank_plan.read_text())['new_feature_status'], 'preguntar_si_hay_funcionalidad_nueva')
            output = work / 'exportacion'
            result_file = work / 'resultados.json'
            result_file.write_text(json.dumps({'C1': 'Aprobado con evidencia'}), encoding='utf-8')
            subprocess.run([sys.executable, str(EXPORT), '--registry', str(registry), '--out', str(output), '--release', '3', '--area', 'Proyecto', '--assigned-to', 'qa@example.test', '--state', 'Design', '--results', str(result_file)], check=True, capture_output=True)
            with (output / 'azure-test-cases.csv').open(encoding='utf-8-sig', newline='') as f: rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['ID'], '')
            self.assertEqual(rows[0]['Work Item Type'], 'Test Case')
            self.assertEqual(rows[0]['Step Expected'], 'Devuelve siete')
            self.assertEqual(rows[0]['Title'], '[C1] Suma con cero')
            with (output / 'registro-pruebas.csv').open(encoding='utf-8-sig', newline='') as f: table = list(csv.DictReader(f))
            self.assertEqual([row['Resultado'] for row in table], ['Aprobado con evidencia', 'Sin resultado individual'])
            trace = json.loads((output / 'trazabilidad.json').read_text())
            self.assertEqual(trace['cases'][0]['references'][0]['source'], source)
            cases['cases'][0]['references'][0]['quote'] = 'Una regla inventada'
            cases_file.write_text(json.dumps(cases), encoding='utf-8')
            invalid = work / 'invalido.json'
            check = subprocess.run([sys.executable, str(VALIDATOR), '--context', str(context_file), '--cases', str(cases_file), '--out', str(invalid)], capture_output=True)
            self.assertEqual(check.returncode, 1)
            self.assertFalse(json.loads(invalid.read_text())['valid'])
            for output, expected_status, expected_code in [('correcto', 'comando_exitoso', 0), ('defecto', 'comando_fallido', 1)]:
                if output == 'defecto':
                    (app / 'calculadora.py').write_text('def sumar(a, b):\n    return a - b\n', encoding='utf-8')
                target = work / output
                run = subprocess.run([sys.executable, str(RUNNER), '--cwd', str(app), '--out', str(target), '--', sys.executable, '-B', '-m', 'unittest', '-v', 'test_calculadora'], capture_output=True)
                self.assertEqual(run.returncode, expected_code)
                self.assertEqual(json.loads((target / 'resultado.json').read_text())['status'], expected_status)
                log = (target / 'stderr.txt').read_text()
                self.assertIn('Ran 2 tests', log)
                self.assertIn('FAIL' if output == 'defecto' else 'OK', log)
                report = (target / 'RESUMEN.md').read_text()
                self.assertIn('FAIL' if output == 'defecto' else 'OK', report)
                if output == 'defecto':
                    self.assertIn('AssertionError', report)
                    self.assertIn('test_suma', report)
            (app / 'calculadora.py').write_text('def sumar(a, b):\n    return a + b\n', encoding='utf-8')
            rerun = work / 'corregido'
            proc = subprocess.run([sys.executable, str(RUNNER), '--cwd', str(app), '--out', str(rerun), '--', sys.executable, '-B', '-m', 'unittest', '-v', 'test_calculadora'], capture_output=True)
            self.assertEqual(proc.returncode, 0)
            self.assertIn('Ran 2 tests', (rerun / 'RESUMEN.md').read_text())
