import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / 'run_tests.py'


class RunnerTests(unittest.TestCase):
    def run_command(self, root, code, timeout='5'):
        output = root / 'resultado'
        proc = subprocess.run([sys.executable, str(RUNNER), '--cwd', str(root), '--out', str(output),
                               '--timeout', timeout, '--', sys.executable, '-c', code], capture_output=True, text=True)
        return proc, json.loads((output / 'resultado.json').read_text()), output

    def test_success_and_failure_are_distinct(self):
        for code, expected, exit_code in [('print("evidencia")', 'comando_exitoso', 0),
                                           ('import sys; print("fallo", file=sys.stderr); sys.exit(7)', 'comando_fallido', 7)]:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                proc, result, out = self.run_command(Path(directory), code)
                self.assertEqual(result['status'], expected)
                self.assertEqual(result['exit_code'], exit_code)
                self.assertEqual(proc.returncode, int(exit_code != 0))
                self.assertTrue((out / 'RESUMEN.md').exists())
                self.assertIn('evidencia' if not exit_code else 'fallo', (out / ('stdout.txt' if not exit_code else 'stderr.txt')).read_text())

    def test_timeout_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proc, result, out = self.run_command(root, 'import time; time.sleep(10)', '1')
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(result['status'], 'tiempo_agotado')
            before = (out / 'resultado.json').read_bytes()
            proc = subprocess.run([sys.executable, str(RUNNER), '--cwd', str(root), '--out', str(out), '--', sys.executable, '-c', 'pass'], capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(before, (out / 'resultado.json').read_bytes())

    def test_missing_executable_records_start_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root / 'resultado'
            proc = subprocess.run([sys.executable, str(RUNNER), '--cwd', str(root), '--out', str(out), '--', str(root / 'no-existe')], capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(json.loads((out / 'resultado.json').read_text())['status'], 'error_inicio')
