"""Pruebas del CLI portable con una aplicación HTTP de fixtures."""

import csv
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import unquote
from zipfile import ZipFile

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
    workflow_calls = []
    secret = "synthetic-bearer-canary"

    def log_message(self, *_):
        pass

    def do_GET(self):
        labels = {
            "/chat-en": "New Chat",
            "/chat-es": "Nuevo Chat",
            "/chat-hidden": "Nuevo Chat",
        }
        if self.path in labels:
            hidden_after_login = json.dumps(self.path == "/chat-hidden")
            html = (
                '<button id="login">Login</button>'
                f'<button id="new-chat" hidden>{labels[self.path]}</button>'
                '<script>document.querySelector("#login").onclick = () => {'
                f'document.querySelector("#new-chat").hidden = {hidden_after_login};'
                '};</script>'
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return
        if self.path == "/interface":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"""<p>Workspace ready</p><button onclick="document.getElementById('result').textContent='Opened'">Expand</button><p id="result"></p>"""
            )
            return
        if self.path in ("/chat-fixture", "/swagger-fixture"):
            swagger = self.path == "/swagger-fixture"
            lead = (
                '<button id="try">Try it out</button><form id="flow" hidden>'
                if swagger
                else '<form id="flow">'
            )
            button = "Execute" if swagger else "Send"
            html = (
                lead
                + f"""
                <input id="message"><button id="send">{button}</button></form>
                <p id="status"></p><pre id="result"></pre>
                <script>
                const form = document.querySelector("#flow");
                const toggle = document.querySelector("#try");
                if (toggle) toggle.onclick = () => form.hidden = false;
                form.onsubmit = async (event) => {{
                    event.preventDefault();
                    const message = document.querySelector("#message").value;
                    const response = await fetch("/fixture-operation", {{
                        method: "POST", headers: {{"Content-Type": "application/json"}},
                        body: JSON.stringify({{message}})
                    }});
                    document.querySelector("#status").innerText = response.status;
                    document.querySelector("#result").innerText = (await response.json()).message;
                }};
                </script>
            """
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
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

    def do_POST(self):
        if self.path != "/fixture-operation":
            self.send_error(404)
            return
        incoming = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).workflow_calls.append(incoming["message"])
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(incoming).encode())


@contextmanager
def application():
    RecordsHandler.attempts = 0
    RecordsHandler.workflow_calls = []
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

    def simulate_model_call(self, identifier):
        now = datetime.now(timezone.utc)
        with self.token_source.open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(
                    {
                        "scope": "qa-fixture",
                        "id": identifier,
                        "input": 30,
                        "output": 5,
                        "start": (now - timedelta(milliseconds=1)).isoformat(),
                        "end": now.isoformat(),
                    }
                )
                + "\n"
            )

    def cli(self, command, *args, data=None, code=0, metered=True):
        if (
            metered
            and command in ("publish", "export-html")
            and hasattr(self, "token_source")
        ):
            self.simulate_model_call("corte-" + str(self.token_source.stat().st_size))
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
            env={**os.environ, "V6_TEST_OPERATOR": RecordsHandler.secret},
            timeout=90,
        )
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        if metered and command == "init" and code == 0:
            self.token_source = self.workspace / "native-usage-fixture.jsonl"
            self.simulate_model_call("primera-llamada")
            self.cli(
                "tokens-check", "--file", str(self.token_source), "--format", "native"
            )
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

    def offline_case(self, identifier="REC-01"):
        case = self.case(identifier)
        del case["http"]
        case["level"] = "integration"
        return case

    def browser_case(self, identifier="WEB-01"):
        case = self.offline_case(identifier)
        case.update(
            title="Abrir el elemento desde la pantalla",
            level="web",
            browser_flow="web_ui",
            browser_path="/interface",
            browser_steps=[{"id": "expand", "type": "click", "control": "expand"}],
            criteria=[
                {
                    "id": "opened",
                    "expected": "Opened visible",
                    "check": {"type": "visible_text", "equals": "Opened"},
                }
            ],
        )
        return case

    @unittest.skipUnless(os.environ.get("QA_V6_TEST_BROWSER"), "Playwright opcional")
    def test_functional_ui_checks_visibility_independently_of_language(self):
        scenarios = [
            ("LOGIN-EN", "/chat-en", 0),
            ("LOGIN-ES", "/chat-es", 0),
            ("LOGIN-HIDDEN", "/chat-hidden", 1),
        ]
        with application() as base_url:
            profile = self.workspace / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "base_url": base_url,
                        "browser_channel": os.environ["QA_V6_TEST_BROWSER"],
                        "browser_paths": [path for _, path, _ in scenarios],
                        "browser_controls": {"login": "#login", "new-chat": "#new-chat"},
                    }
                ),
                encoding="utf-8",
            )
            self.cli("init", "--title", "Login localizado", "--profile", str(profile))
            cases = []
            for identifier, path, _ in scenarios:
                case = self.browser_case(identifier)
                case.update(
                    browser_path=path,
                    browser_steps=[{"id": "login", "type": "click", "control": "login"}],
                    criteria=[
                        {
                            "id": "new-chat",
                            "expected": "El control para iniciar un chat está visible.",
                            "check": {"type": "control_visible", "control": "new-chat"},
                        }
                    ],
                )
                cases.append(case)
            self.cli("record", data=cases)
            self.cli("freeze-plan")
            for identifier, _, code in scenarios:
                with self.subTest(case=identifier):
                    self.cli(
                        "execute", "--case", identifier, "--via", "playwright", code=code
                    )

    @unittest.skipUnless(os.environ.get("QA_V6_TEST_BROWSER"), "Playwright opcional")
    def test_publish_preserves_retry_and_sanitizes_artifacts(self):
        with application() as base_url:
            profile = self.workspace / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "base_url": base_url,
                        "browser_channel": os.environ["QA_V6_TEST_BROWSER"],
                        "browser_paths": ["/interface"],
                        "browser_controls": {"expand": "button"},
                        "credentials": {
                            "operator": "V6_TEST_OPERATOR",
                            "viewer": "V6_TEST_VIEWER",
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
            self.cli("preflight", "--browser")
            self.cli("index")
            queries = self.run_dir / "queries.json"
            queries.write_text('["lectura registros"]', encoding="utf-8")
            artifact = Path(self.cli("pack", "--queries", str(queries)).stdout.strip())
            self.assertTrue(
                json.loads(artifact.read_text(encoding="utf-8"))["passages"]
            )
            self.cli("record", data=[self.case(), self.browser_case()])
            self.cli("execute", "--case", "REC-01", "--via", "http", code=2)
            self.assertEqual(RecordsHandler.attempts, 0)

            catalog = self.run_dir / "requirements.json"
            catalog.write_text('["REQ-READ","REQ-WRITE"]', encoding="utf-8")
            self.cli("freeze-plan", "--requirements", str(catalog))
            self.assertEqual(RecordsHandler.attempts, 0)
            self.cli("execute", "--case", "WEB-01", "--via", "playwright")
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
        self.assertEqual(len(all_files), 15)
        self.assertTrue(
            all(path.suffix in {".md", ".xml", ".json", ".html"} for path in all_files)
        )
        self.assertFalse(
            any(
                RecordsHandler.secret in path.read_text(encoding="utf-8")
                for path in all_files
            )
        )
        final = (self.delivery / "informe final.md").read_text(encoding="utf-8")
        self.assertIn("| failed | 1 | 0 |", final)
        self.assertIn("| passed | 1 | 2 |", final)
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

    @unittest.skipUnless(os.environ.get("QA_V6_TEST_BROWSER"), "Playwright opcional")
    def test_playwright_walk_publishes_observed_steps(self):
        with application() as base_url:
            profile = self.workspace / "browser-profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "base_url": base_url,
                        "browser_paths": ["/interface"],
                        "browser_channel": os.environ["QA_V6_TEST_BROWSER"],
                        "browser_controls": {"expand": "button"},
                    }
                ),
                encoding="utf-8",
            )
            self.cli("init", "--title", "Interfaz", "--profile", str(profile))
            preflight = Path(self.cli("preflight", "--browser").stdout.strip())
            channel = os.environ["QA_V6_TEST_BROWSER"]
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
            self.cli("record", data=[case, self.browser_case()])
            self.cli("freeze-plan")
            self.cli("execute", "--case", "WEB-01", "--via", "playwright")
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
        case = self.offline_case()
        case["rationale"] = (
            "Confirmar la lectura antes de habilitar el flujo siguiente."
        )
        self.cli(
            "record",
            data=[
                case,
                self.offline_case("REC-02"),
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
            "execution_method": "cli",
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
            ],
        )
        self.cli(
            "record",
            data={**defect, "id": "F-05", "fix_status": "verified_fixed"},
            code=2,
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
        self.assertIn("Casos del plan con ejecución observada</dt><dd>1 de 2", report)
        self.assertIn("Casos del plan sin ejecución observada · REC-02", report)
        self.assertIn("contrato.md · líneas 1–2", report)
        self.assertIn("Se probó la consulta. Queda pendiente", report)
        self.assertIn('<a href="#case-REC-01">REC-01</a>', report)
        self.assertIn("build-fixture", report)
        self.cli("publish")
        final = (self.delivery / "informe final.md").read_text(encoding="utf-8")
        self.assertIn("Se probó la consulta. Queda pendiente", final)
        self.assertIn("Casos del plan con ejecución observada · 1 de 2", final)
        self.assertIn("Casos del plan sin ejecución observada · REC-02", final)

        fixes = Path(self.cli("export-fixes").stdout.strip())
        self.assertEqual(fixes, (self.harness / "SDD fixes" / "demo").resolve())
        self.assertEqual(
            {path.name for path in fixes.iterdir()},
            {"F-01.md", "F-02.md", "evidencias"},
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
        reviewed_html = reviewed_report.read_text(encoding="utf-8")
        self.assertIn("Evidencia inválida", reviewed_html)
        self.assertIn("Casos del plan con ejecución observada</dt><dd>0 de 2", reviewed_html)

    def test_export_azure_keeps_case_steps_and_metadata(self):
        self.cli("init", "--title", "Casos de Azure")
        batch = self.offline_case()
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
        login = self.offline_case("REC-02")
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

    def test_api_only_plan_and_browser_preflight_stop_without_playwright(self):
        with application() as base_url:
            profile = self.workspace / "preflight.json"
            profile.write_text(
                json.dumps(
                    {
                        "base_url": base_url,
                        "http_operations": [
                            {
                                "method": "GET",
                                "path": "/availability",
                                "probe": {"status": 204},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.cli("init", "--title", "API", "--profile", str(profile))
            self.cli("record", data=self.case())
            self.cli("freeze-plan")
            self.cli("preflight")
            self.assertTrue((self.run_dir / "plan.json").is_file())

    @unittest.skipUnless(os.environ.get("QA_V6_TEST_BROWSER"), "Playwright opcional")
    def test_orchestrates_web_swagger_database_fixtures_and_evidence(self):
        with application() as base_url:
            database = self.workspace / "qa.sqlite"
            with sqlite3.connect(database) as connection:
                connection.executescript(
                    "CREATE TABLE records (id TEXT, status TEXT); INSERT INTO records VALUES ('QA-1', 'ready');"
                )
            profile = self.workspace / "profile.json"
            operation = {"method": "POST", "path": "/fixture-operation"}
            profile.write_text(
                json.dumps(
                    {
                        "base_url": base_url,
                        "browser_channel": os.environ["QA_V6_TEST_BROWSER"],
                        "browser_paths": ["/chat-fixture", "/swagger-fixture"],
                        "browser_controls": {
                            "try": "#try",
                            "input": "#message",
                            "send": "#send",
                            "result": "#result",
                        },
                        "http_operations": [operation],
                        "database": {
                            "driver": "sqlite",
                            "path": str(database.resolve()),
                            "queries": {
                                "record": {
                                    "table": "records",
                                    "columns": ["status"],
                                    "where": ["id"],
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.cli("init", "--title", "Orquestación", "--profile", str(profile))
            self.cli("preflight", "--browser")

            spec = self.workspace / "mock.json"
            spec.write_text(
                '{"id":{"type":"sequence"},"number":{"type":"integer","min":3,"max":9}}',
                encoding="utf-8",
            )
            for name in ("fixture-a", "fixture-b"):
                self.cli(
                    "mock-data", "--name", name, "--spec", str(spec), "--seed", "38"
                )
            a = (self.run_dir / "fixtures" / "fixture-a.json").read_bytes()
            b = (self.run_dir / "fixtures" / "fixture-b.json").read_bytes()
            self.assertEqual(a, b)

            cases = []
            for name, field, path, message in (
                ("WEB-01", "web_ui", "/chat-fixture", "QA web"),
                ("SWAGGER-01", "swagger_ui", "/swagger-fixture", "QA Swagger"),
            ):
                swagger = field == "swagger_ui"
                case = self.browser_case(name)
                case.update(
                    browser_flow=field,
                    browser_path=path,
                    browser_operation=operation,
                    browser_steps=[
                        *(
                            [{"id": "try", "type": "click", "control": "try"}]
                            if swagger
                            else []
                        ),
                        {
                            "id": "write",
                            "type": "fill",
                            "control": "input",
                            "value": message,
                        },
                        {"id": "send", "type": "click", "control": "send"},
                    ],
                    criteria=[
                        {
                            "id": "visible",
                            "expected": "Resultado visible",
                            "check": {
                                "type": "control_text",
                                "control": "result",
                                "equals": message,
                            },
                        },
                        {
                            "id": "http",
                            "expected": "HTTP 201",
                            "check": {"type": "network_status", "equals": 201},
                        },
                    ],
                )
                cases.append(case)
            db_case = self.offline_case("DB-01")
            db_case.update(
                db={"query": "record", "parameters": {"id": "QA-1"}},
                criteria=[
                    {
                        "id": "rows",
                        "expected": "Una fila",
                        "check": {"type": "row_count", "equals": 1},
                    },
                    {
                        "id": "status",
                        "expected": "Estado ready",
                        "check": {
                            "type": "json_equals",
                            "path": [0, "status"],
                            "equals": "ready",
                        },
                    },
                ],
            )
            self.cli("record", data=[*cases, db_case])
            self.cli(
                "freeze-plan",
                "--browser-flow",
                "web_ui",
                "--browser-flow",
                "swagger_ui",
            )
            self.cli("execute", "--case", "DB-01", "--via", "db")
            manifest = self.run_dir / "orquestacion.json"
            manifest.write_text(
                json.dumps(
                    [
                        {"case": "WEB-01", "via": "playwright"},
                        {"case": "SWAGGER-01", "via": "playwright"},
                        {"case": "DB-01", "via": "db"},
                    ]
                ),
                encoding="utf-8",
            )
            self.cli("suite", "--manifest", str(manifest))
            self.assertEqual(RecordsHandler.workflow_calls, ["QA web", "QA Swagger"])

        archive = Path(self.cli("publish", "--zip").stdout.strip())
        with ZipFile(archive) as bundle:
            self.assertIsNone(bundle.testzip())
            for report in REPORTS:
                self.assertIn(f"demo/{report}", bundle.namelist())
            html = bundle.read("demo/reporte gerencial.html").decode("utf-8")
            for fragment in (
                "Resumen", "WEB-01", "SWAGGER-01", "DB-01", "Escenario y pasos"
            ):
                self.assertIn(fragment, html)
            for prefix in ("WEB-01", "SWAGGER-01", "DB-01", "preflight"):
                self.assertTrue(
                    any(
                        name.startswith(f"demo/evidencias/{prefix}-")
                        for name in bundle.namelist()
                    )
                )
        db_evidence = next((self.delivery / "evidencias").glob("DB-01-*.md"))
        self.assertIn("Filas observadas · 1", db_evidence.read_text(encoding="utf-8"))
        swagger_evidence = next(
            (self.delivery / "evidencias").glob("SWAGGER-01-*.md")
        ).read_text(encoding="utf-8")
        self.assertIn("| try | click | observed |", swagger_evidence)
        self.assertIn(
            "HTTP de la operación observada en el navegador · 201", swagger_evidence
        )

    @unittest.skipUnless(os.environ.get("QA_V6_TEST_BROWSER"), "Playwright opcional")
    def test_suite_continues_when_swagger_is_unavailable(self):
        with application() as base_url:
            operation = {
                "method": "GET",
                "path": "/records/demo",
                "actors": ["operator"],
            }
            profile = self.workspace / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "base_url": base_url,
                        "browser_channel": os.environ["QA_V6_TEST_BROWSER"],
                        "browser_paths": ["/swagger-ausente"],
                        "browser_controls": {"execute": "#execute"},
                        "http_operations": [operation],
                        "credentials": {"operator": "V6_TEST_OPERATOR"},
                    }
                ),
                encoding="utf-8",
            )
            self.cli("init", "--title", "Swagger ausente", "--profile", str(profile))
            self.cli("preflight", "--browser")
            swagger = self.browser_case("SWAGGER-01")
            swagger.update(
                browser_flow="swagger_ui",
                browser_path="/swagger-ausente",
                browser_operation={"method": "GET", "path": "/records/demo"},
                browser_steps=[
                    {"id": "execute", "type": "click", "control": "execute"}
                ],
                criteria=swagger["criteria"]
                + [
                    {
                        "id": "status",
                        "expected": "HTTP 200",
                        "check": {"type": "network_status", "equals": 200},
                    }
                ],
            )
            self.cli("record", data=[swagger, self.case()])
            self.cli("freeze-plan", "--browser-flow", "swagger_ui")
            manifest = self.run_dir / "suite.json"
            manifest.write_text(
                '[{"case":"SWAGGER-01","via":"playwright"},{"case":"REC-01","via":"http"}]',
                encoding="utf-8",
            )
            self.cli("suite", "--manifest", str(manifest), code=1)
            self.assertEqual(RecordsHandler.attempts, 1)
            self.assertTrue(list((self.run_dir / "evidencias").glob("REC-01-*.md")))
            self.cli("publish", "--zip", code=3)
            self.assertIn(
                "Swagger UI",
                (self.delivery / "informe final.md").read_text(encoding="utf-8"),
            )

    def test_requires_native_tokens_and_reports_only_the_selected_otel_calls(self):
        self.cli("init", "--title", "Medición", "--benchmark", metered=False)
        self.assertIn(
            "fuente de tokens verificada", self.cli("preflight", code=3).stderr
        )
        self.cli("record", data=self.offline_case())
        self.cli("freeze-plan", code=2)
        file = self.workspace / "otel.jsonl"

        def emit(rows):
            with file.open("a", encoding="utf-8") as stream:
                for row in rows:
                    stream.write(json.dumps(row) + "\n")

        def span(trace, identifier, session, inputs, outputs, operation="chat"):
            now = datetime.now(timezone.utc)
            return {
                "type": "span",
                "traceId": trace,
                "spanId": identifier,
                "startTime": (now - timedelta(milliseconds=1)).isoformat(),
                "endTime": now.isoformat(),
                "attributes": {
                    "gen_ai.operation.name": operation,
                    **({"gen_ai.conversation.id": session} if session else {}),
                    "gen_ai.usage.input_tokens": inputs,
                    "gen_ai.usage.output_tokens": outputs,
                    "gen_ai.request.model": "requested-alias",
                    "gen_ai.response.model": "resolved-test-model",
                    "gen_ai.input.messages": "Canary private input.",
                },
            }

        first = span("t1", "native-request-1", "qa-a", 50, 5)
        emit([first, first, span("t2", "other", "qa-b", 6000, 6000)])
        self.cli("tokens-check", "--file", str(file), code=3)
        self.cli("tokens-check", "--file", str(file), "--scope", "qa-a")
        self.cli("preflight")
        self.cli("freeze-plan")
        stale = self.cli("publish", "--zip", "--name", "incompleto", code=3)
        self.assertTrue(Path(stale.stdout.strip()).is_file())
        self.cli("tokens-stage", "--stage", "analisis")
        second = span("t3", "native-request-2", None, 60, 6)
        emit([second, span("t3", "root", "qa-a", 999, 999, "invoke_agent")])
        archive = Path(self.cli("publish", "--zip").stdout.strip())
        with ZipFile(archive) as bundle:
            metrics = bundle.read("demo/metricas.md").decode()
            evidence = bundle.read("demo/evidencias/consumo-tokens-v6.md").decode()
            self.assertIn("Total observado · 121", metrics)
            self.assertIn("| Lectura y análisis | 1 | 60 | 6 | 66 |", metrics)
            self.assertNotIn("native-request", evidence)
            self.assertNotIn("Canary private input.", evidence)
            self.assertNotIn("otel.jsonl", evidence)
            self.assertIn("resolved-test-model", evidence)
            self.assertNotIn("requested-alias", evidence)

        emit([span("t4", "missing-output", "qa-a", 10, None)])
        self.cli("publish", "--name", "parcial", code=3)
        incomplete = (self.delivery.parent / "parcial" / "metricas.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("1 llamada(s) sin contador completo", incomplete)
        self.assertIn("Subtotal observado · 121", incomplete)

    def test_evaluates_models_with_frozen_inputs_and_independent_review(self):
        shutil.copytree(
            HARNESS / "evaluate-llm",
            self.harness / "evaluate-llm",
            ignore=shutil.ignore_patterns("__pycache__", "resultados"),
        )
        evaluator = self.harness / "evaluate-llm" / "evaluate.py"

        def evaluate(command, *options, code=0):
            result = subprocess.run(
                [sys.executable, evaluator, command, *options],
                capture_output=True,
                text=True,
                timeout=25,
            )
            self.assertEqual(result.returncode, code, result.stdout + result.stderr)
            return result

        corpus = self.workspace / "corpus"
        corpus.mkdir()
        (corpus / "contrato.md").write_text(
            "# Registros\n\nEl operador puede consultar el registro demo.",
            encoding="utf-8",
        )
        self.cli(
            "init",
            "--title",
            "Evaluación",
            "--version",
            "build-01",
            "--environment",
            "qa-fixture",
            "--corpus",
            str(corpus),
            metered=False,
        )
        index = self.cli("index")
        revision = json.loads(Path(index.stdout.strip()).read_text())["revision"]
        # Se obtiene la revisión antes de iniciar la sesión que se va a evaluar.
        shutil.rmtree(self.run_dir)
        self.cli(
            "init",
            "--title",
            "Evaluación",
            "--version",
            "build-01",
            "--environment",
            "qa-fixture",
            "--corpus",
            str(corpus),
            metered=False,
        )
        model = "resolved-model/v1"
        source = self.workspace / "native.jsonl"

        def call(identifier, observed=model):
            now = datetime.now(timezone.utc)
            row = {
                "id": identifier,
                "scope": "private-benchmark-conversation",
                "start": (now - timedelta(milliseconds=1)).isoformat(),
                "end": now.isoformat(),
                "input": 100,
                "output": 20,
                "model": observed,
                "message": "private-prompt-canary",
            }
            with source.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row) + "\n")

        config = self.workspace / "benchmark.json"
        task = self.workspace / "consigna.md"
        task.write_text("Validar el flujo de registros.\n", encoding="utf-8")
        spec = json.loads(
            (self.harness / "evaluate-llm" / "benchmark.ejemplo.json").read_text()
        )
        spec.update(
            id="comparacion",
            version="build-01",
            environment="qa-fixture",
            corpus_revision=revision,
            browser_flows=[],
        )
        config.write_text(json.dumps(spec))
        evaluate("congelar", "--config", config, "--consigna", task)
        call("private-first")
        self.cli("tokens-check", "--format", "native", "--file", str(source))
        prepare = (
            "--benchmark",
            "comparacion",
            "--run",
            self.run_dir,
            "--modelo",
            "Qwen",
        )
        self.assertIn(
            "no confirma",
            evaluate(
                "preparar",
                *prepare[:-1],
                "Alias",
                "--modelo-esperado",
                "gui-label",
                code=2,
            ).stderr,
        )
        (self.run_dir / "evaluate-llm.json").unlink()
        evaluate("preparar", *prepare, "--modelo-esperado", model)
        self.cli("tokens-stage", "--stage", "analisis")
        self.cli("index")
        queries = self.workspace / "queries.json"
        queries.write_text('["operador registro demo"]')
        self.cli("pack", "--queries", str(queries))
        call("analysis")
        self.cli("tokens-stage", "--stage", "diseno")
        self.cli("record", data=self.offline_case())
        self.cli("freeze-plan")
        call("design")
        self.cli("tokens-stage", "--stage", "ejecucion")
        evidence = "evidencias/record-observed.md"
        (self.run_dir / evidence).write_text(
            "El contrato respondió con el registro demo.\n"
        )
        observed_at = datetime.now(timezone.utc).isoformat()
        self.cli(
            "record",
            data={
                "kind": "execution",
                "case_id": "REC-01",
                "status": "failed",
                "executor": "agent",
                "execution_method": "cli",
                "started_at": observed_at,
                "finished_at": observed_at,
                "observation": "Se observó una diferencia esperada por el fixture.",
                "results": [
                    {
                        "id": item["id"],
                        "status": "failed",
                        "evidence": evidence,
                        "observation": "Resultado observado.",
                    }
                    for item in self.offline_case()["criteria"]
                ],
            },
        )
        call("execution")
        self.cli("tokens-stage", "--stage", "cierre")
        evaluate("finalizar", "--run", "demo")
        self.assertIn(
            "no alcanza el cierre",
            evaluate("archivar", "--run", self.run_dir, code=2).stderr,
        )
        call("closure")
        archived = Path(evaluate("archivar", "--run", self.run_dir).stdout.strip())
        self.assertEqual(
            archived.parts[-4:], ("comparacion", "modelos", "Qwen", "demo")
        )
        summary = json.loads((archived / "medicion.json").read_text())
        self.assertEqual(summary["issues"], [])
        self.assertEqual(summary["total_input"], 500)
        self.assertEqual(summary["stages"]["ejecucion"]["output"], 20)
        self.assertEqual(summary["cases"][0]["result"], "failed")
        self.assertTrue((archived / "reporte gerencial.html").is_file())
        self.assertNotIn("private-", (archived / "medicion.json").read_text())

        review = self.workspace / "review.json"
        reviewed = {
            "reviewer": "QA independiente",
            "checks": {
                "A1": {
                    "met": True,
                    "reason": "Fuente",
                    "evidence": ["analisis segundo cerebro.md"],
                    "cases": [],
                },
                "D1": {
                    "met": True,
                    "reason": "Caso",
                    "evidence": ["casos.md"],
                    "cases": ["REC-01"],
                },
                "E1": {
                    "met": True,
                    "reason": "Evidencia",
                    "evidence": ["ejecuciones.md"],
                    "cases": ["REC-01"],
                },
            },
        }
        review.write_text(json.dumps(reviewed))
        review_args = (
            "--benchmark",
            "comparacion",
            "--modelo",
            "Qwen",
            "--id",
            "demo",
            "--archivo",
            review,
        )
        evaluate("revisar", *review_args, code=2)
        reviewed["checks"]["E1"]["evidence"] = [evidence]
        review.write_text(json.dumps(reviewed))
        evaluate("revisar", *review_args)
        chart = Path(evaluate("comparar", "--benchmark", "comparacion").stdout.strip())
        self.assertIn("600.0", chart.read_text())
        self.assertIn("100.0%", chart.read_text())
        self.assertIn("120.0 (n=1)", chart.with_suffix(".md").read_text())

        # Un segundo resultado portable con una conversación e identidad distintas.
        second = archived.parent.parent / "Sonnet" / "sonnet-01"
        second.mkdir(parents=True)
        alternate = {
            **summary,
            "run": "sonnet-01",
            "label": "Sonnet",
            "expected_model": "another-resolved-model",
            "conversation_sha256": "2" * 64,
            "total_input": 700,
        }
        (second / "medicion.json").write_text(json.dumps(alternate))
        evaluate("comparar", "--benchmark", "comparacion")
        self.assertIn("Sonnet · another-resolved-model", chart.read_text())
        self.assertIn("800.0", chart.read_text())

        call("another-model", "foreign-model")
        mixed_run = self.run_dir.with_name("mixta")
        shutil.copytree(self.run_dir, mixed_run)
        self.assertIn(
            "distinta o mezclada",
            evaluate("archivar", "--run", mixed_run, code=2).stderr,
        )
        evaluate("archivar", "--run", mixed_run, "--incompleta")
        evaluate("comparar", "--benchmark", "comparacion")
        self.assertIn("misma conversación", chart.read_text())
        self.assertNotIn("Qwen · resolved-model/v1", chart.read_text())
        self.assertIn("Sin datos para este gráfico.", chart.read_text())

    def test_blocked_run_publishes_without_profile_or_plan(self):
        self.cli("init", "--title", "Entorno sin acceso", "--benchmark", metered=False)
        self.cli(
            "record",
            data={
                "kind": "note",
                "phase": "acceso",
                "observation": "El entorno no está disponible.",
            },
        )
        self.cli("publish", code=3)
        self.assertEqual(
            {path.name for path in self.delivery.iterdir()},
            REPORTS | {"junit.xml", "resultado.json", "reporte gerencial.html"},
        )
        html = (self.delivery / "reporte gerencial.html").read_text(encoding="utf-8")
        self.assertIn("Recomendación para la release · inconclusa", html)
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
        incomplete = self.offline_case()
        del incomplete["priority"]
        self.cli("record", data=incomplete, code=2)
        pending = self.offline_case()
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
