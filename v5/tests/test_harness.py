"""Pruebas del CLI portable con una aplicación HTTP de fixtures."""

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import unquote

HARNESS = Path(__file__).resolve().parents[1]
REPORTS = {
    "analisis segundo cerebro.md",
    "casos.md",
    "ejecuciones.md",
    "informe final.md",
    "log.md",
    "metricas.md",
    "plan casos.md",
}


class RecordsHandler(BaseHTTPRequestHandler):
    attempts = 0
    secret = "synthetic-bearer-canary"

    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path == "/interface":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<p>Workspace ready</p><button>Expand</button>")
            return
        if self.path == "/availability":
            self.send_response(204)
            self.end_headers()
            return
        if (
            self.path != "/records/demo"
            or self.headers.get("Authorization") != "Bearer " + self.secret
        ):
            self.send_error(401)
            return
        type(self).attempts += 1
        self.send_response(400 if self.attempts == 1 else 200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"id": "demo", "private": self.secret}).encode())


@contextmanager
def application():
    RecordsHandler.attempts = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), RecordsHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


class PortableHarnessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.harness = self.workspace / "framework-copy"
        for folder in ("src", "templates"):
            shutil.copytree(
                HARNESS / folder,
                self.harness / folder,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        self.run_dir = self.harness / ".trabajo" / "demo"
        self.delivery = self.harness / "resultados" / "demo"

    def cli(self, command, *args, data=None, code=0):
        result = subprocess.run(
            [
                sys.executable,
                str(self.harness / "src" / "qa.py"),
                command,
                "--run",
                "demo",
                *args,
            ],
            check=False,
            cwd=self.workspace,
            input=json.dumps(data) if data is not None else None,
            capture_output=True,
            text=True,
            env={**os.environ, "V5_TEST_OPERATOR": RecordsHandler.secret},
            timeout=15,
        )
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def case(self, case_id="REC-01"):
        return {
            "kind": "case",
            "id": case_id,
            "title": "Leer registro sintético",
            "feature": "Registros",
            "requirement": "REQ-READ",
            "priority": "high",
            "level": "api",
            "scenario": "QA con operador y registro demo",
            "preconditions": ["El fixture demo existe."],
            "steps": ["Consultar el registro con el rol operador."],
            "expected": "Devuelve el registro solicitado.",
            "oracle_status": "documented",
            "sources": [{"path": "contrato.md", "start": 1, "end": 2}],
            "http": {"method": "GET", "path": "/records/demo", "actor": "operator"},
            "criteria": [
                {
                    "id": "status",
                    "expected": "HTTP 200",
                    "check": {"type": "status", "equals": 200},
                },
                {
                    "id": "record",
                    "expected": "id igual a demo",
                    "check": {"type": "json_equals", "path": ["id"], "equals": "demo"},
                },
            ],
        }

    def test_publish_preserves_retry_and_copies_only_markdown(self):
        with application() as base_url:
            profile = self.workspace / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "base_url": base_url,
                        "credentials": {
                            "operator": "V5_TEST_OPERATOR",
                            "viewer": "V5_TEST_VIEWER",
                        },
                        "http_operations": [
                            {
                                "method": "GET",
                                "path": "/availability",
                                "probe": {"status": 204},
                            },
                            {
                                "method": "GET",
                                "path": "/records/demo",
                                "actors": ["operator"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            corpus = self.workspace / "corpus"
            corpus.mkdir()
            (corpus / "contrato.md").write_text(
                "# Registros\nLectura de un registro.", encoding="utf-8"
            )
            self.cli(
                "init",
                "--title",
                "Registros",
                "--version",
                "build-42",
                "--profile",
                str(profile),
                "--corpus",
                str(corpus),
            )
            self.cli("preflight")
            self.cli("index")
            queries = self.run_dir / "queries.json"
            queries.write_text('["lectura registros"]', encoding="utf-8")
            artifact = Path(self.cli("pack", "--queries", str(queries)).stdout.strip())
            self.assertTrue(
                json.loads(artifact.read_text(encoding="utf-8"))["passages"]
            )
            self.cli("record", data=self.case())
            self.cli("execute", "--case", "REC-01", "--via", "http", code=2)
            self.assertEqual(RecordsHandler.attempts, 0)

            catalog = self.run_dir / "requirements.json"
            catalog.write_text('["REQ-READ","REQ-WRITE"]', encoding="utf-8")
            self.cli("freeze-plan", "--requirements", str(catalog))
            invalid_actor = self.case("REC-02")
            invalid_actor["http"]["actor"] = "viewer"
            self.cli("record", data=invalid_actor)
            self.cli("execute", "--case", "REC-02", "--via", "http", code=2)
            self.assertEqual(RecordsHandler.attempts, 0)
            self.cli("execute", "--case", "REC-01", "--via", "http", code=1)
            failed_evidence = next((self.run_dir / "evidencias").glob("REC-01-*.md"))
            self.cli(
                "record",
                data={
                    "kind": "finding",
                    "id": "F-01",
                    "case_ids": ["REC-01"],
                    "classification": "product",
                    "confidence": "confirmed",
                    "observation": "El primer intento devolvió HTTP 400.",
                    "interpretation": "Contrato divergente en el primer intento.",
                    "pending": "Verificar estabilidad.",
                    "evidence": "evidencias/" + failed_evidence.name,
                },
            )
            manifest = self.run_dir / "suite.json"
            manifest.write_text('[{"case":"REC-01","via":"http"}]', encoding="utf-8")
            self.cli("suite", "--manifest", str(manifest))

        (self.run_dir / "evidencias" / "sin-referencia.md").write_text(
            "No se publica.", encoding="utf-8"
        )
        self.cli("publish")
        self.assertEqual({path.name for path in self.delivery.glob("*.md")}, REPORTS)
        all_files = [path for path in self.delivery.rglob("*") if path.is_file()]
        self.assertEqual(len(all_files), 10)
        self.assertTrue(all(path.suffix == ".md" for path in all_files))
        self.assertFalse(
            any(
                RecordsHandler.secret in path.read_text(encoding="utf-8")
                for path in all_files
            )
        )
        final = (self.delivery / "informe final.md").read_text(encoding="utf-8")
        self.assertIn("| failed | 1 | 0 |", final)
        self.assertIn("| passed | 0 | 1 |", final)
        self.assertIn("REQ-WRITE", final)
        self.assertIn("F-01", final)
        self.assertNotIn(
            "REC-02", (self.delivery / "plan casos.md").read_text(encoding="utf-8")
        )
        self.assertIn(
            "REC-02", (self.delivery / "casos.md").read_text(encoding="utf-8")
        )
        attempts = (self.delivery / "ejecuciones.md").read_text(encoding="utf-8")
        self.assertIn("intento 1", attempts)
        self.assertIn("intento 2", attempts)
        for path in self.delivery.glob("*.md"):
            for reference in re.findall(
                r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")
            ):
                self.assertTrue(
                    (self.delivery / unquote(reference)).is_file(), reference
                )

        failed_evidence.unlink()
        self.cli("publish", "--name", "demo-revisado", code=1)
        revised = (
            self.delivery.parent / "demo-revisado" / "informe final.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Evidencia ausente", revised)
        self.assertIn("| invalid_evidence | 1 | 0 |", revised)
        self.assertTrue((self.delivery / "evidencias" / failed_evidence.name).is_file())

    @unittest.skipUnless(os.environ.get("QA_V5_TEST_BROWSER"), "Playwright opcional")
    def test_playwright_walk_publishes_observed_steps(self):
        with application() as base_url:
            profile = self.workspace / "browser-profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "base_url": base_url,
                        "browser_paths": ["/interface"],
                        "browser_channel": os.environ["QA_V5_TEST_BROWSER"],
                        "browser_controls": {"expand": "button"},
                    }
                ),
                encoding="utf-8",
            )
            self.cli("init", "--title", "Interfaz", "--profile", str(profile))
            preflight = Path(self.cli("preflight", "--browser").stdout.strip())
            channel = os.environ["QA_V5_TEST_BROWSER"]
            self.assertIn(
                f"Navegador · Listo · {channel}", preflight.read_text(encoding="utf-8")
            )
            case = self.case()
            case["level"] = "ui"
            case["browser_path"] = "/interface"
            case["browser_walk"] = {
                "seed": 13,
                "actions": [
                    {"id": "read", "type": "click", "control": "expand"},
                    {"id": "viewport", "type": "resize", "width": 800, "height": 600},
                ],
            }
            case["criteria"] = [
                {
                    "id": "visible",
                    "expected": "Mensaje visible",
                    "check": {"type": "visible_text", "equals": "Workspace ready"},
                },
                {
                    "id": "walk",
                    "expected": "Recorrido completo",
                    "check": {"type": "walk_completed"},
                },
                {
                    "id": "errors",
                    "expected": "Sin excepciones JS",
                    "check": {"type": "no_page_errors"},
                },
            ]
            self.cli("record", data=case)
            self.cli("freeze-plan")
            self.cli(
                "execute", "--case", "REC-01", "--via", "playwright", "--seed", "25"
            )
        self.cli("publish")
        evidence = next((self.delivery / "evidencias").glob("REC-01-*.md")).read_text(
            encoding="utf-8"
        )
        self.assertIn("Semilla · 25", evidence)
        self.assertIn("| read | observed |", evidence)
        self.assertIn("| viewport | observed |", evidence)

    def test_exports_gerencial_report_and_only_open_product_fixes(self):
        self.cli(
            "init",
            "--title",
            "Aplicación <script>alert(1)</script>",
            "--version",
            "build-fixture",
        )
        case = self.case()
        case["rationale"] = (
            "Confirmar la lectura antes de habilitar el flujo siguiente."
        )
        self.cli(
            "record",
            data=[
                case,
                self.case("REC-02"),
                {
                    "kind": "note",
                    "phase": "resumen-gerencial",
                    "observation": "Se probó la consulta. Queda pendiente repetirla después del arreglo.",
                },
            ],
        )
        self.cli("freeze-plan")
        evidence = self.run_dir / "evidencias" / "REC-01-observado.md"
        evidence.write_text("# Evidencia\n\nHTTP 400 observado.\n", encoding="utf-8")
        reference = "evidencias/" + evidence.name
        execution = {
            "kind": "execution",
            "case_id": "REC-01",
            "status": "failed",
            "executor": "agent",
            "execution_method": "http",
            "observation": "HTTP 400 al consultar un registro existente.",
            "started_at": "2026-01-15T10:00:00-03:00",
            "finished_at": "2026-01-15T10:00:01-03:00",
            "results": [
                {
                    "id": criterion["id"],
                    "status": "failed",
                    "observation": "Observado HTTP 400.",
                    "evidence": reference,
                }
                for criterion in case["criteria"]
            ],
        }
        defect = {
            "kind": "finding",
            "id": "F-01",
            "case_ids": ["REC-01"],
            "classification": "product",
            "confidence": "confirmed",
            "observation": "Un registro válido devuelve HTTP 400.",
            "interpretation": "El estado HTTP diverge del contrato.",
            "pending": "Repetir REC-01 con el build corregido.",
            "evidence": reference,
        }
        self.cli(
            "record",
            data=[
                execution,
                {
                    **defect,
                    "sdd": {
                        "title": "Preservar el estado HTTP de la consulta",
                        "component": "Controlador de registros",
                        "suggestion": "Revisar el manejo del estado cuando el registro existe.",
                        "acceptance": ["El operador recibe HTTP 200."],
                        "regression": ["Reejecutar REC-01 con un fixture sintético."],
                        "sources": [
                            {"path": "src/records.py", "locator": "get_record"}
                        ],
                    },
                },
                {**defect, "id": "F-02"},
                {**defect, "id": "F-03", "classification": "runner"},
                {**defect, "id": "F-04", "confidence": "hypothesis"},
                {**defect, "id": "F-05", "fix_status": "verified_fixed"},
            ],
        )
        report_path = Path(self.cli("export-html").stdout.strip())
        self.assertEqual(
            report_path, (self.harness / "reportes" / "demo.html").resolve()
        )
        report = report_path.read_text(encoding="utf-8")
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", report)
        self.assertNotIn("<script>", report)
        self.assertNotIn("<script src", report)
        self.assertIn(
            "Confirmar la lectura antes de habilitar el flujo siguiente.", report
        )
        self.assertIn("HTTP 400 al consultar un registro existente.", report)
        self.assertIn("Intentos y criterios (1)", report)
        self.assertIn("No se registró un intento para este caso.", report)
        self.assertIn("Se probó la consulta. Queda pendiente", report)
        self.assertIn('<a href="#case-REC-01">REC-01</a>', report)
        self.assertIn("build-fixture", report)

        fixes = Path(self.cli("export-fixes").stdout.strip())
        self.assertEqual(fixes, (self.harness / "SDD fixes" / "demo").resolve())
        self.assertEqual(
            {path.name for path in fixes.iterdir()}, {"F-01.md", "F-02.md"}
        )
        spec = (fixes / "F-01.md").read_text(encoding="utf-8")
        for expected in (
            "Preservar el estado HTTP de la consulta",
            "REC-01 (REQ-READ)",
            "contrato.md · líneas 1–2",
            r"src/records.py · get\_record",
            "El operador recibe HTTP 200.",
            "Reejecutar REC-01",
            "Un registro válido devuelve HTTP 400.",
        ):
            self.assertIn(expected, spec)
        self.assertIn(
            "Borrador pendiente de completar",
            (fixes / "F-02.md").read_text(encoding="utf-8"),
        )

        evidence.unlink()
        result = self.cli("export-fixes", "--name", "revisado", code=1)
        self.assertIn(
            "F-01 · Propuesta pendiente por evidencia inválida.", result.stdout
        )
        self.assertFalse((fixes.parent / "revisado").exists())
        reviewed_report = Path(
            self.cli("export-html", "--name", "revisado", code=1).stdout.strip()
        )
        self.assertIn("Evidencia inválida", reviewed_report.read_text(encoding="utf-8"))

    def test_export_azure_keeps_case_steps_and_metadata(self):
        self.cli("init", "--title", "Casos de Azure")
        batch = self.case()
        batch.update(
            title="Lote de altas, un titular",
            preconditions=["Worker disponible.", "Fixture sintético preparado."],
            steps=[
                'Adjuntar archivo "nómina.csv".',
                "Consultar la respuesta.\nRevisar código.",
            ],
            step_expected=["Se procesa el archivo.", "Código 1000, sin errores."],
            azure={
                "test_case_type": "Positive",
                "functionality": "Admitir",
                "component_type": "API",
                "type": "Functional",
            },
        )
        login = self.case("REC-02")
        login.update(
            title="Verificar inicio de sesión",
            preconditions=[],
            steps=["Iniciar sesión.", "Cerrar sesión."],
            expected="Se muestra el ingreso.",
        )
        self.cli("record", data=[batch, login])
        self.cli("freeze-plan")
        self.cli("publish")
        result = self.cli("export-azure", "--area", r"Proyecto\Área QA")
        target = Path(result.stdout.strip())
        self.assertEqual(target, (self.harness / "azure" / "demo.csv").resolve())
        self.assertTrue(target.read_bytes().startswith(b"\xef\xbb\xbf"))
        with target.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            rows = list(reader)
            self.assertEqual(
                reader.fieldnames,
                [
                    "ID",
                    "Work Item Type",
                    "Title",
                    "Test Step",
                    "Step Action",
                    "Step Expected",
                    "Area Path",
                    "Assigned To",
                    "State",
                    "Tipo de caso de prueba",
                    "Funcionalidad",
                    "Tipo de componente",
                    "Tipo",
                ],
            )
        self.assertEqual([row["Test Step"] for row in rows], ["1", "2", "3", "1", "2"])
        self.assertTrue(
            all(row["ID"] == "" and row["Assigned To"] == "" for row in rows)
        )
        self.assertTrue(
            all(
                row["Work Item Type"] == "Test Case" and row["State"] == "Design"
                for row in rows
            )
        )
        self.assertTrue(all(row["Area Path"] == r"Proyecto\Área QA" for row in rows))
        self.assertEqual([row["Title"] for row in rows[:3]], [batch["title"]] * 3)
        self.assertEqual(
            rows[0]["Step Action"],
            "Precondiciones:\n- Worker disponible.\n- Fixture sintético preparado.",
        )
        self.assertEqual([row["Step Action"] for row in rows[1:3]], batch["steps"])
        self.assertEqual(
            [row["Step Expected"] for row in rows],
            ["", *batch["step_expected"], "", login["expected"]],
        )
        self.assertEqual(
            [
                rows[1][column]
                for column in (
                    "Tipo de caso de prueba",
                    "Funcionalidad",
                    "Tipo de componente",
                    "Tipo",
                )
            ],
            ["Positive", "Admitir", "API", "Functional"],
        )
        self.assertEqual(rows[3]["Funcionalidad"], login["feature"])
        self.assertFalse(list(self.delivery.rglob("*.csv")))
        self.assertIn(
            "Código 1000, sin errores.",
            (self.delivery / "casos.md").read_text(encoding="utf-8"),
        )

        self.cli("export-azure", "--area", "Otra Área", code=2)
        result = self.cli(
            "export-azure",
            "--area",
            "Otra Área",
            "--name",
            "otra-area",
            "--assigned-to",
            "qa@example.test",
            "--state",
            "Proposed",
        )
        with Path(result.stdout.strip()).open(
            encoding="utf-8-sig", newline=""
        ) as source:
            row = next(csv.DictReader(source))
            self.assertEqual(
                (row["Assigned To"], row["State"]), ("qa@example.test", "Proposed")
            )

    def test_export_azure_rejects_ambiguous_titles_and_misaligned_steps(self):
        self.cli("init", "--title", "Casos de Azure")
        malformed = self.case()
        malformed["step_expected"] = []
        self.cli("record", data=malformed, code=2)
        self.cli("record", data=[self.case(), self.case("REC-02")])
        result = self.cli("export-azure", "--area", "Proyecto QA", code=2)
        self.assertIn("Título de Azure duplicado", result.stderr)
        self.assertFalse((self.harness / "azure" / "demo.csv").exists())

    def test_blocked_run_publishes_without_profile_or_plan(self):
        self.cli("init", "--title", "Entorno sin acceso")
        self.cli(
            "record",
            data={
                "kind": "note",
                "phase": "acceso",
                "observation": "El entorno no está disponible.",
            },
        )
        self.cli("publish")
        self.assertEqual({path.name for path in self.delivery.iterdir()}, REPORTS)
        self.assertIn(
            "El entorno no está disponible.",
            (self.delivery / "log.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "No hay un plan congelado.",
            (self.delivery / "plan casos.md").read_text(encoding="utf-8"),
        )

    def test_pending_oracle_and_generic_case_validation(self):
        self.cli("init", "--title", "Contrato pendiente")
        incomplete = self.case()
        del incomplete["priority"]
        self.cli("record", data=incomplete, code=2)
        pending = self.case()
        pending.update(
            oracle_status="pending",
            oracle_pending_reason="El contrato debe confirmarse.",
            sources=[],
        )
        self.cli("record", data=pending)
        self.cli("freeze-plan")
        self.cli(
            "record",
            data={
                "kind": "execution",
                "case_id": "REC-01",
                "status": "blocked",
                "executor": "agent",
                "execution_method": "http",
                "observation": "Falta confirmar el contrato.",
                "results": [
                    {
                        "id": criterion["id"],
                        "status": "blocked",
                        "observation": "Oráculo pendiente.",
                    }
                    for criterion in pending["criteria"]
                ],
            },
        )
        self.cli("publish")
        final = (self.delivery / "informe final.md").read_text(encoding="utf-8")
        self.assertIn("| blocked | 1 | 1 |", final)
