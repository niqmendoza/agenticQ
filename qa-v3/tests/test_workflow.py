import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "src" / "qa.py"


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.corpus = self.root / "corpus"
        self.corpus.mkdir()
        (self.corpus / "policy.md").write_text(
            "# Acceso\nSólo el dueño puede leer.\n", encoding="utf-8"
        )
        self.run = self.root / "run"

    def command(self, *args, ok=True):
        result = subprocess.run(
            [sys.executable, str(CLI), *map(str, args)], text=True, capture_output=True
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def init(self):
        self.command(
            "init", "--corpus", self.corpus, "--run", self.run, "--title", "Ensayo"
        )

    def event(self, obj, ok=True):
        path = self.root / "event.json"
        path.write_text(json.dumps(obj), encoding="utf-8")
        return self.command("record", "--run", self.run, "--json", path, ok=ok)

    def test_full_session_and_latest_attempt(self):
        self.init()
        self.command("index", "--run", self.run)
        queries = self.root / "queries.json"
        queries.write_text('["acceso dueño"]', encoding="utf-8")
        self.command("pack", "--run", self.run, "--queries", queries)
        packet = json.loads((self.run / "artifacts" / "002-pack.json").read_text())
        self.assertTrue(packet["passages"])
        self.event(
            {
                "kind": "case",
                "id": "C1",
                "title": "Acceso",
                "expected": "Leer",
                "oracle_status": "documented",
                "sources": ["policy.md:2"],
            }
        )
        for status in ("failed", "passed"):
            self.event(
                {
                    "kind": "execution",
                    "case_id": "C1",
                    "status": status,
                    "observation": status,
                    "evidence": "captura",
                }
            )
        self.event(
            {
                "kind": "finding",
                "id": "H1",
                "observation": "Error",
                "evidence": "captura",
                "interpretation": "Sin causa confirmada",
                "pending": "Investigar",
            }
        )
        log = (self.run / "log.md").read_text()
        self.assertIn("aprobados 1, fallidos 0", log)
        self.assertIn("Intentos registrados: 2. Hallazgos registrados: 1", log)
        self.assertIn("Sin causa confirmada", log)
        with (self.run / "casos.csv").open(encoding="utf-8-sig", newline="") as stream:
            cases = list(csv.DictReader(stream))
        with (self.run / "ejecuciones.csv").open(
            encoding="utf-8-sig", newline=""
        ) as stream:
            attempts = list(csv.DictReader(stream))
        self.assertEqual((cases[0]["id"], cases[0]["estado"]), ("C1", "passed"))
        self.assertEqual([row["estado"] for row in attempts], ["failed", "passed"])

    def test_rejects_invalid_records_and_corpus_output(self):
        self.command(
            "init",
            "--corpus",
            self.corpus,
            "--run",
            self.corpus / "run",
            "--title",
            "No",
            ok=False,
        )
        self.init()
        self.event(
            {
                "kind": "execution",
                "case_id": "missing",
                "status": "passed",
                "observation": "x",
                "evidence": "x",
            },
            ok=False,
        )
        result = self.event({"kind": []}, ok=False)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(len(json.loads((self.run / "events.json").read_text())), 1)
        self.event(
            {
                "kind": "case",
                "id": "C1",
                "title": "x",
                "expected": "x",
                "oracle_status": "wrong",
                "sources": ["x"],
            },
            ok=False,
        )

    def test_changed_corpus_stops_pack_and_records_failure(self):
        self.init()
        self.command("index", "--run", self.run)
        (self.corpus / "policy.md").write_text("Contenido modificado", encoding="utf-8")
        queries = self.root / "q.json"
        queries.write_text('["acceso"]', encoding="utf-8")
        self.command("pack", "--run", self.run, "--queries", queries, ok=False)
        events = json.loads((self.run / "events.json").read_text())
        self.assertNotEqual(events[-1]["exit_code"], 0)
        self.assertIn("fallida", events[-1]["observation"])

    def test_batch_is_atomic_and_can_reference_earlier_case(self):
        self.init()
        case = {
            "kind": "case",
            "id": "C1",
            "title": "x",
            "expected": "x",
            "oracle_status": "pending",
            "sources": ["sin fuente"],
        }
        execution = {
            "kind": "execution",
            "case_id": "C1",
            "status": "blocked",
            "observation": "sin entorno",
            "evidence": "pendiente",
        }
        self.event([case, {**execution, "status": "inventado"}], ok=False)
        self.assertEqual(len(json.loads((self.run / "events.json").read_text())), 1)
        self.event([case, execution])
        self.assertIn("bloqueados 1", (self.run / "log.md").read_text())

    def test_csv_preserves_plan_and_escapes_spreadsheet_formulas(self):
        self.init()
        self.event(
            {
                "kind": "case",
                "id": "C2",
                "title": "=ejemplo",
                "feature": "Chat",
                "steps": ["Entrar", "Enviar"],
                "expected": "Respuesta",
                "oracle_status": "pending",
                "sources": ["pendiente"],
            }
        )
        with (self.run / "casos.csv").open(encoding="utf-8-sig", newline="") as stream:
            row = next(csv.DictReader(stream))
        self.assertEqual(row["titulo"], "'=ejemplo")
        self.assertEqual(row["funcionalidad"], "Chat")
        self.assertEqual(row["estado"], "sin_ejecutar")
        self.assertEqual(json.loads(row["pasos"]), ["Entrar", "Enviar"])


if __name__ == "__main__":
    unittest.main()
