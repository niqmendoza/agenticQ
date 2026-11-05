import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]


class JUnitCircuito(unittest.TestCase):
    def test_pruebas_reales_a_csv_individual(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Un ejecutor sintético genera XML a partir de resultados reales de unittest.
            runner = root / 'test_real.py'
            runner.write_text(textwrap.dedent('''
                import sys, unittest, xml.etree.ElementTree as ET
                class Pruebas(unittest.TestCase):
                    def test_ok(self): self.assertEqual(1 + 1, 2)
                    def test_falla(self): self.assertEqual(1, 2)
                    @unittest.skip('pendiente')
                    def test_omitida(self): pass
                class Reporte(unittest.TestResult):
                    def __init__(self): super().__init__(); self.xml = ET.Element('testsuite')
                    def item(self, test): return ET.SubElement(self.xml, 'testcase', classname='Pruebas', name=test._testMethodName)
                    def addSuccess(self, test): super().addSuccess(test); self.item(test)
                    def addFailure(self, test, err): super().addFailure(test, err); ET.SubElement(self.item(test), 'failure').text = self._exc_info_to_string(err, test)
                    def addError(self, test, err): super().addError(test, err); ET.SubElement(self.item(test), 'error').text = self._exc_info_to_string(err, test)
                    def addSkip(self, test, reason): super().addSkip(test, reason); ET.SubElement(self.item(test), 'skipped', message=reason)
                result = Reporte(); unittest.defaultTestLoader.loadTestsFromTestCase(Pruebas).run(result)
                ET.ElementTree(result.xml).write(sys.argv[1], encoding='utf-8', xml_declaration=True)
                sys.exit(0 if result.wasSuccessful() else 1)
            '''), encoding='utf-8')
            xml = root / 'junit.xml'
            run = subprocess.run([sys.executable, str(SCRIPTS/'run_tests.py'), '--cwd', str(root), '--out', str(root/'run'), '--', sys.executable, str(runner), str(xml)], capture_output=True)
            self.assertEqual(run.returncode, 1)
            mapping = {'C1': {'classname':'Pruebas','name':'test_ok'}, 'C2': {'classname':'Pruebas','name':'test_falla'}, 'C3': {'classname':'Pruebas','name':'test_omitida'}, 'C4': {'classname':'Pruebas','name':'test_ausente'}}
            mp = root/'map.json'; mp.write_text(json.dumps(mapping), encoding='utf-8')
            parsed = root/'individuales'
            subprocess.run([sys.executable, str(SCRIPTS/'resultados_junit.py'), '--junit', str(xml), '--map', str(mp), '--out', str(parsed)], check=True, capture_output=True)
            values = json.loads((parsed/'resultados.json').read_text())
            self.assertEqual(list(values.values()), ['Aprobada','Falló','Omitida','Sin resultado individual'])
            cases = [{'id': cid, 'title': cid, 'steps':['Hacer'], 'expected':'Observar', 'feature':'Ejemplo', 'tests':'test_real.py', 'references':[]} for cid in mapping]
            registry = root/'reg.json'; registry.write_text(json.dumps({'schema':'qa-regression/1','application':'Ejemplo','cases':cases}))
            export = root/'csv'
            subprocess.run([sys.executable, str(SCRIPTS/'exportar.py'), '--registry', str(registry), '--out', str(export), '--release', 'R1', '--results', str(parsed/'resultados.json'), '--executed', str(parsed/'ejecutadas.json'), '--evidence', str(parsed/'evidencias.json')], check=True, capture_output=True)
            with (export/'registro-pruebas.csv').open(encoding='utf-8-sig', newline='') as f: rows = list(csv.DictReader(f))
            self.assertEqual([r['Resultado'] for r in rows], list(values.values()))
            self.assertIn('Pruebas::test_falla', rows[1]['Qué se ejecutó'])
            self.assertIn('SHA-256', rows[1]['Evidencia'])
            self.assertIn('No ejecutada', rows[2]['Qué se ejecutó'])
            self.assertFalse((export/'azure-test-cases.csv').exists())

    def test_duplicado_y_mapeo_inseguro(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); xml = root/'j.xml'
            xml.write_text('<testsuite><testcase classname="C" name="n"/><testcase classname="C" name="n"/></testsuite>')
            mp = root/'map.json'; mp.write_text(json.dumps({'X':{'classname':'C','name':'n'}}))
            subprocess.run([sys.executable, str(SCRIPTS/'resultados_junit.py'),'--junit',str(xml),'--map',str(mp),'--out',str(root/'out')], check=True, capture_output=True)
            self.assertIn('ambiguo', json.loads((root/'out'/'resultados.json').read_text())['X'])
            mp.write_text(json.dumps({'X':{'classname':'C','name':'n'},'Y':{'classname':'C','name':'n'}}))
            self.assertNotEqual(subprocess.run([sys.executable,str(SCRIPTS/'resultados_junit.py'),'--junit',str(xml),'--map',str(mp),'--out',str(root/'other')],capture_output=True).returncode, 0)
