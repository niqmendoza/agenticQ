"""Prueba el contrato de release y los límites entre V5 y V6 desde el CLI público."""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from test_harness import application, HARNESS


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.catalog = self.root / "catalogo"
        self.catalog.mkdir()
        (self.catalog / "reglas.md").write_text("Un registro debe tener estado listo.")
        self.db = self.root / "producto.sqlite"
        with sqlite3.connect(self.db) as connection:
            connection.execute(
                "CREATE TABLE registros (id TEXT PRIMARY KEY, estado TEXT)"
            )
            connection.execute("INSERT INTO registros VALUES ('QA-1', 'pendiente')")
        self.case = {
            "kind": "case",
            "id": "REG-01",
            "title": "Estado de solicitud",
            "scenario": "Registro de prueba",
            "priority": "critical",
            "level": "integration",
            "feature": "Solicitudes",
            "requirement": "EST-01",
            "steps": ["Leer el registro de prueba."],
            "expected": "Estado listo",
            "preconditions": [],
            "oracle_status": "documented",
            "sources": [{"path": "reglas.md", "locator": "estado listo"}],
            "db": {"query": "registro", "parameters": {"id": "QA-1"}},
            "criteria": [
                {
                    "id": "estado",
                    "expected": "listo",
                    "check": {
                        "type": "json_equals",
                        "path": [0, "estado"],
                        "equals": "listo",
                    },
                }
            ],
        }
        self.config = {
            "schema": "agentic-qc/suite-1",
            "app": "solicitudes",
            "profile": "perfil.json",
            "corpus": ".",
            "cases": "casos.json",
            "manifest": "pasos.json",
        }
        self.profile = {
            "database": {
                "driver": "sqlite",
                "path": str(self.db),
                "queries": {
                    "registro": {
                        "table": "registros",
                        "columns": ["estado"],
                        "where": ["id"],
                    }
                },
            }
        }
        for name, data in [
            ("suite", self.config),
            ("perfil", self.profile),
            ("casos", [self.case]),
            ("pasos", [{"case": "REG-01", "via": "db"}]),
        ]:
            self.put(name, data)

    def put(self, name, data):
        (self.catalog / (name + ".json")).write_text(json.dumps(data))

    def cli(self, *args, code=0):
        result = subprocess.run(
            [sys.executable, HARNESS / "src/qa.py", *map(str, args)],
            cwd=self.root,
            capture_output=True,
            text=True,
            env={**os.environ, "QC_WORKSPACE": str(self.root / "qc")},
        )
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def run_build(self, build, code):
        self.cli(
            "run",
            "--suite",
            self.catalog / "suite.json",
            "--env",
            "QA",
            "--build",
            build,
            "--id",
            build,
            code=code,
        )
        return self.root / "qc/resultados" / build

    def test_retest_requires_matching_fixture_and_passing_evidence(self):
        failed = self.run_build("A", 1)
        self.assertTrue((failed / "triage/REG-01.md").is_file())
        result = json.loads((failed / "resultado.json").read_text())
        evidence = result["cases"][0]["evidence"]
        finding = {
            "kind": "finding",
            "id": "F1",
            "case_ids": ["REG-01"],
            "classification": "product",
            "confidence": "confirmed",
            "observation": "Estado incorrecto",
            "interpretation": "Difiere de la regla",
            "pending": "Retest",
            "evidence": evidence,
        }
        self.put("hallazgo", finding)
        self.cli("record", "--run", "A", "--json", self.catalog / "hallazgo.json")
        self.cli("export-fixes", "--run", "A")
        fixes = self.root / "qc/SDD fixes/A"
        self.assertTrue((fixes / evidence).exists())
        self.assertIn("qc run", (fixes / "F1.md").read_text())
        self.cli("verify-fix", "--run", "A", "--finding", "F1", "--retest", "A", code=2)
        with sqlite3.connect(self.db) as connection:
            connection.execute("UPDATE registros SET estado='listo'")
        fixed = self.run_build("B", 0)
        with ZipFile(fixed.with_suffix(".zip")) as z:
            self.assertIn("B/junit.xml", z.namelist())
        self.cli("verify-fix", "--run", "A", "--finding", "F1", "--retest", "B")
        self.assertIn(
            "No hay defectos",
            self.cli("export-fixes", "--run", "A", "--name", "cerrados").stdout,
        )
        self.cli("verify-fix", "--run", "A", "--finding", "F1", "--retest", "B", code=2)
        exp = {
            "app": "solicitudes",
            "environment": "QA",
            "healthy_build": "B",
            "regressions": {"estado": {"build": "A"}},
            "trials": [
                {
                    "model": "fixture-model",
                    "id": "ensayo",
                    "reviewed_cases": {"estado": ["REG-01"]},
                    "results": {
                        "healthy": str(fixed / "resultado.json"),
                        "estado": str(failed / "resultado.json"),
                    },
                }
            ],
        }
        self.put("experimento", exp)
        self.cli(
            "score-models",
            "--experiment",
            self.catalog / "experimento.json",
            "--out",
            self.root / "calidad.md",
        )
        self.assertIn("100.0%", (self.root / "calidad.md").read_text())

    def test_incomplete_scope_and_source_validation(self):
        self.case["sources"][0]["locator"] = "cita ausente"
        self.put("casos", [self.case])
        self.cli("validate", "--suite", self.catalog / "suite.json", code=2)
        self.case["sources"][0]["locator"] = "estado listo"
        self.put("casos", [self.case])
        self.config["requirements"] = "req.json"
        self.put("suite", self.config)
        self.put("req", ["EST-01", "EST-02"])
        with sqlite3.connect(self.db) as connection:
            connection.execute("UPDATE registros SET estado='listo'")
        folder = self.run_build("incompleta", 3)
        self.assertEqual(
            json.loads((folder / "resultado.json").read_text())["missing_requirements"],
            ["EST-02"],
        )

    def test_v5_published_zip_and_promoted_cases(self):
        baseline = self.root / "base.zip"
        with ZipFile(baseline, "w") as out:
            out.writestr(
                "base/informe final.md", "- Entorno · QA\n- Versión o build · A\n"
            )
            out.writestr(
                "base/casos.md",
                "| REG-01 | Lectura | Inicial | failed | passed | 2 |\n",
            )
        folder = self.run_build("A", 1)
        file = self.root / "comparacion.md"
        self.cli(
            "compare",
            "--baseline",
            baseline,
            "--candidate",
            folder.with_suffix(".zip"),
            "--out",
            file,
        )
        self.assertIn(
            "failed → passed (2) | failed → failed (1) | Sin huella verificable",
            file.read_text(),
        )
        source = self.root / "qc/.trabajo/A"
        target = self.root / "promovida"
        self.cli(
            "promote",
            "--from-run",
            source,
            "--manifest",
            self.catalog / "pasos.json",
            "--app",
            "solicitudes",
            "--out",
            target,
        )
        self.cli("validate", "--suite", target / "suite.json", "--corpus", self.catalog)

    def test_regression_repo_runs_saved_and_new_cases_then_repeats_approved_catalog(self):
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE registros SET estado = 'listo'")
        repo = self.root / "regresiones"
        suite = self.catalog / "suite.json"

        def run_release(build, *extra, code=0):
            self.cli(
                "run", "--app", "solicitudes", "--regressions", repo, "--corpus",
                self.catalog, "--env", "QA", "--build", build, "--id", build,
                *extra, code=code,
            )
            return self.root / "qc/resultados" / build

        def save(build, case, code=0):
            self.cli(
                "promote", "--app", "solicitudes", "--regressions", repo,
                "--from-run", self.root / "qc/.trabajo" / build, "--case", case,
                code=code,
            )

        run_release("primera", "--new-suite", suite)
        self.cli(
            "promote", "--app", "otra-aplicacion", "--regressions", repo,
            "--from-run", self.root / "qc/.trabajo/primera", "--case", "REG-01", code=2,
        )
        save("primera", "REG-01")
        save("primera", "REG-01")  # Un reintento conserva el catálogo.
        lots = repo / "solicitudes/lotes"
        first = (lots / "primera/casos.json").read_bytes()
        self.cli(
            "validate", "--app", "solicitudes", "--regressions", repo,
            "--corpus", self.catalog, "--new-suite", suite, code=2,
        )
        with sqlite3.connect(self.db) as db:
            db.execute("INSERT INTO registros VALUES ('QA-2', 'pendiente')")
        case = {
            **self.case,
            "id": "REG-02",
            "title": "Caso de la nueva release",
            "expected": "Estado archivado",
            "db": {"query": "registro", "parameters": {"id": "QA-2"}},
        }
        case["criteria"] = [
            {
                "id": "estado",
                "expected": "archivado",
                "check": {
                    "type": "json_equals", "path": [0, "estado"], "equals": "archivado"
                },
            }
        ]
        self.put("casos", [case])
        self.put("pasos", [{"case": "REG-02", "via": "db"}])
        run_release("fallo", "--new-suite", suite, code=1)
        save("fallo", "REG-02", code=2)
        self.assertEqual(sorted(path.name for path in lots.iterdir()), ["primera"])

        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE registros SET estado = 'archivado' WHERE id = 'QA-2'")
        output = run_release("segunda", "--new-suite", suite)
        self.assertIn("2 de 2", (output / "reporte gerencial.html").read_text())
        self.assertEqual(
            json.loads((output / "resultado.json").read_text())["provenance"]["regressions"],
            {"saved": ["REG-01"], "new": ["REG-02"]},
        )
        save("segunda", "REG-02")
        self.assertEqual((lots / "primera/casos.json").read_bytes(), first)
        replayed = run_release("tercera")
        result = json.loads((replayed / "resultado.json").read_text())
        self.assertEqual(
            [(row["case"], row["status"]) for row in result["cases"]],
            [("REG-01", "passed"), ("REG-02", "passed")],
        )

    @unittest.skipUnless(
        os.environ.get("QA_V6_TEST_BROWSER"), "Integración Playwright opcional"
    )
    def test_api_captures_id_and_resolves_it_in_dependent_case(self):
        with application() as url:
            case = {
                **self.case,
                "http": {"method": "POST", "path": "/fixture-operation"},
                "criteria": [
                    {
                        "id": "estado",
                        "expected": "201",
                        "check": {"type": "status", "equals": 201},
                    }
                ],
            }
            del case["db"]
            second = {
                **case,
                "id": "REG-02",
                "criteria": [
                    {
                        "id": "id",
                        "expected": "Devuelve el ID capturado",
                        "check": {
                            "type": "json_equals",
                            "path": ["message"],
                            "equals": "{{registro}}",
                        },
                    }
                ],
            }
            self.put("casos", [case, second])
            self.put("perfil", {"base_url": url, "http_operations": [case["http"]]})
            self.put("inicial", {"message": "{{RUN_ID}}"})
            self.put("sig", {"message": "{{registro}}"})
            self.put(
                "pasos",
                [
                    {
                        "case": "REG-01",
                        "via": "api",
                        "body": "inicial.json",
                        "capture": {"registro": ["message"]},
                    },
                    {
                        "case": "REG-02",
                        "via": "api",
                        "depends_on": ["REG-01"],
                        "body": "sig.json",
                    },
                ],
            )
            folder = self.run_build("QA-001", 0)
            rows = json.loads((folder / "resultado.json").read_text())["cases"]
            self.assertEqual([r["status"] for r in rows], ["passed", "passed"])
