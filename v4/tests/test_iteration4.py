from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import threading

from test_workflow import CLI


class Handler(BaseHTTPRequestHandler):
    requests = []

    def do_GET(self):
        self.requests.append(self.path)
        self.send_response(200)
        self.send_header(
            "Content-Type", "text/html" if self.path == "/spa" else "application/json"
        )
        self.end_headers()
        self.wfile.write(
            b"<html>OK</html>" if self.path == "/spa" else b'{"status":"ok"}'
        )

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        reject = self.path == "/validate" and type(body.get("name")) is not str
        self.send_response(422 if reject else 200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            b'{"error":{"code":"invalid_type","field":"name"}}'
            if reject
            else b'{"status":"ok"}'
        )

    def log_message(self, *args):
        pass


class Iteration4Tests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
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

    def event(self, event, ok=True):
        path = self.root / "event.json"
        path.write_text(json.dumps(event))
        return self.command("record", "--run", self.run, "--json", path, ok=ok)

    def new_profile(self, origin):
        profile = self.root / "profile.json"
        profile.write_text(
            json.dumps(
                {
                    "base_url": origin,
                    "http_operations": [
                        {"method": "GET", "path": "/health", "probe": True},
                        {"method": "GET", "path": "/spa"},
                        {"method": "POST", "path": "/validate"},
                        {"method": "POST", "path": "/accept"},
                    ],
                    "db_sources": ["qa-db.read_summary"],
                }
            )
        )
        self.command("init", "--run", self.run, "--profile", profile, "--title", "API")

    def test_http_asserts_json_and_respects_profile(self):
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                self.new_profile(f"http://127.0.0.1:{server.server_port}")
                cases = json.loads(
                    (
                        Path(__file__).parents[1] / "examples/casos-iteracion4.json"
                    ).read_text()
                )
                case = cases[0]
                self.event(case)
                self.command("preflight", "--run", self.run)
                preflight = json.loads((self.run / "preflight.json").read_text())
                self.assertEqual(preflight["probes"][0]["state"], "ready")
                self.command("freeze-plan", "--run", self.run)
                frozen = (self.run / "plan-casos.csv").read_bytes()
                self.command(
                    "execute", "--run", self.run, "--case", case["id"], "--via", "http"
                )
                for identifier, path, code in (("SPA", "/spa", 1), ("OUT", "/out", 2)):
                    self.event(
                        {
                            **case,
                            "id": identifier,
                            "http": {"method": "GET", "path": path},
                        }
                    )
                    result = self.command(
                        "execute",
                        "--run",
                        self.run,
                        "--case",
                        identifier,
                        "--via",
                        "http",
                        ok=False,
                    )
                    self.assertEqual(result.returncode, code)
                self.assertNotIn("/out", Handler.requests)
                self.assertIn(b"sin_ejecutar", frozen)
                self.assertEqual((self.run / "plan-casos.csv").read_bytes(), frozen)
                events = json.loads((self.run / "events.json").read_text())
                executions = [event for event in events if event["kind"] == "execution"]
                self.assertEqual(
                    [event["status"] for event in executions], ["passed", "failed"]
                )
                self.assertEqual(
                    [c["status"] for c in executions[-1]["results"]],
                    ["passed", "failed", "failed"],
                )
                self.assertGreaterEqual(executions[-1]["duration_ms"], 0)
            finally:
                server.shutdown()
                worker.join()

    def test_wrong_type_must_be_rejected_by_contract(self):
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                self.new_profile(f"http://127.0.0.1:{server.server_port}")
                examples = Path(__file__).parents[1] / "examples/validacion-tipos"
                wrong = self.root / "wrong.json"
                self.command(
                    "fixture-variant",
                    "--fixture",
                    examples / "valido.json",
                    "--path",
                    '["name"]',
                    "--value",
                    "7",
                    "--out",
                    wrong,
                )
                self.assertEqual(json.loads(wrong.read_text()), {"name": 7})
                case = json.loads((examples / "caso.json").read_text())
                self.event(case)
                self.command(
                    "execute",
                    "--run",
                    self.run,
                    "--case",
                    "TIPO-01",
                    "--via",
                    "http",
                    "--body",
                    wrong,
                )
                case.update(
                    id="TIPO-ACEPTADO", http={"method": "POST", "path": "/accept"}
                )
                self.event(case)
                result = self.command(
                    "execute",
                    "--run",
                    self.run,
                    "--case",
                    "TIPO-ACEPTADO",
                    "--via",
                    "http",
                    "--body",
                    wrong,
                    ok=False,
                )
                self.assertEqual(result.returncode, 1)
            finally:
                server.shutdown()
                worker.join()

    def test_strict_plan_and_external_results(self):
        self.new_profile("http://127.0.0.1:8080")
        case = {
            "kind": "case",
            "id": "DB",
            "title": "Fixture",
            "expected": "Conteo y estado",
            "oracle_status": "documented",
            "sources": [{"path": "spec.md", "start": 1, "end": 4}],
            "steps": ["Consultar la vista de QA."],
            "requirement": "REQ-DB",
            "criteria": [
                {"id": "count", "expected": "Conteo conocido"},
                {"id": "state", "expected": "Estado visible"},
            ],
        }
        self.event({**case, "requirement": ""}, ok=False)
        self.event(case)
        (self.run / "proof.json").write_text('{"row_count": 1}')
        execution = {
            "kind": "execution",
            "case_id": "DB",
            "status": "partial",
            "execution_method": "mcp_db",
            "db_source": "qa-db.read_summary",
            "started_at": "2026-11-12T13:00:00Z",
            "finished_at": "2026-11-12T13:00:01Z",
            "duration_ms": 1000,
            "observation": "Conteo observado.",
            "evidence": "proof.json",
            "results": [
                {
                    "id": "count",
                    "status": "passed",
                    "observation": "Coincide.",
                    "evidence": "proof.json",
                },
                {
                    "id": "state",
                    "status": "blocked",
                    "observation": "Columna no disponible.",
                },
            ],
        }
        self.event({**execution, "status": "passed"}, ok=False)
        self.event({**execution, "db_source": "otro"}, ok=False)
        self.event(execution)
        self.assertIn("REQ-DB", (self.run / "requisitos.csv").read_text())
        self.assertIn("parciales 1", (self.run / "log.md").read_text())
        catalog = self.root / "catalog.json"
        catalog.write_text(json.dumps(["REQ-DB", "REQ-SIN-CASO"]))
        self.command("audit", "--run", self.run, "--requirements", catalog)
        report = json.loads((self.run / "audit.json").read_text())
        self.assertEqual(report["catalog_without_cases"], ["REQ-SIN-CASO"])
        (self.run / "proof.json").unlink()
        self.command("audit", "--run", self.run, "--requirements", catalog, ok=False)
        report = json.loads((self.run / "audit.json").read_text())
        self.assertEqual(report["case_status"], {"invalid_evidence": 1})
