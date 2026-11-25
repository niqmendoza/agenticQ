"""Controles del contrato entre etapas con archivos y CLI reales."""

import csv
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

V9 = Path(__file__).resolve().parents[2]


class FlujoV9(unittest.TestCase):
    def setUp(self):
        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.root = Path(temporal.name)
        self.v9 = self.root / "v9"
        shutil.copytree(
            V9,
            self.v9,
            ignore=shutil.ignore_patterns("logs", "salidas", "credenciales.txt", "__pycache__", "*.zip"),
        )
        self.a = self.v9 / "01-analisis"
        self.b = self.v9 / "02-casos"
        self.c = self.v9 / "03-ejecuciones"
        self.analisis = self.a / "salidas" / "piloto"
        self.revision = self.a / "ejemplos/revision.demo.json"
        self.diseno = json.loads((self.b / "ejemplos/diseno.demo.json").read_text())

    def cli(self, script, *args, codigo=0, aislado=False):
        cmd = (
            [sys.executable]
            + (["-S"] if aislado else [])
            + [str(script), *map(str, args)]
        )
        r = subprocess.run(cmd, check=False, capture_output=True, text=True)
        self.assertEqual(r.returncode, codigo, r.stdout + r.stderr)
        return r

    def analizar(self, codigo=0):
        self.cli(
            self.a / "scripts/analizar.py",
            "procesar",
            "--id",
            "piloto",
            "--encargo",
            self.a / "ejemplos/encargo.demo.json",
            "--corpus",
            self.a / "ejemplos/corpus",
            "--revision",
            self.revision,
            codigo=codigo,
        )

    def preparar(self, *extras, codigo=0):
        path = self.root / "diseno.json"
        path.write_text(json.dumps(self.diseno))
        return self.cli(
            self.b / "scripts/preparar.py",
            "procesar",
            "--id",
            "casos",
            "--analisis",
            self.analisis,
            "--diseno",
            path,
            *extras,
            codigo=codigo,
        )

    def test_csv_ejecucion_bloqueada_y_consumo(self):
        self.analizar()
        self.preparar()
        paquete = self.b / "salidas/casos"
        with (paquete / "casos-qa.csv").open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows[0]), 13)
        self.assertEqual([r["Paso"] for r in rows], ["1", "2", "3"])
        self.assertTrue(rows[0]["Acción"].startswith("Precondiciones:\n"))
        self.assertEqual(
            rows[-1]["Resultado esperado"], self.diseno["casos"][0]["step_expected"][-1]
        )
        self.cli(
            self.c / "scripts/ejecutar.py",
            "procesar",
            "--id",
            "sin-browser",
            "--casos",
            paquete,
            codigo=3,
            aislado=True,
        )
        info = json.loads((self.c / "salidas/sin-browser/dictamen.json").read_text())
        self.assertEqual(
            (info["intentos"], info["preflight"]["navegador"]), (0, "bloqueado")
        )
        row = {
            "scope": "solo-diseno",
            "id": "call",
            "start": "2026-11-24T12:00:00Z",
            "end": "2026-11-24T12:00:03Z",
            "input": 20,
            "output": 3,
        }
        path = self.root / "otel-normalizado.jsonl"
        path.write_text((json.dumps(row) + "\n") * 2)
        r = self.cli(
            self.b / "scripts/preparar.py",
            "medir",
            "--id",
            "casos",
            "--archivo",
            path,
            "--formato",
            "native",
            "--scope",
            "solo-diseno",
        )
        self.assertEqual(
            json.loads(Path(r.stdout.strip()).read_text())["tokens_entrada"], 20
        )
        (paquete / "casos-qa.csv").write_text("cambio")
        self.cli(
            self.c / "scripts/ejecutar.py",
            "procesar",
            "--id",
            "alterado",
            "--casos",
            paquete,
            codigo=2,
        )

    def test_recupera_dos_reglas_lejanas_del_mismo_manual(self):
        corpus = self.root / "corpus"
        corpus.mkdir()
        lineas = ["Texto de contexto."] * 240
        lineas[130] = "Regla alfa: conservar el identificador."
        lineas[215] = "Regla beta: mostrar el estado."
        (corpus / "manual.md").write_text("\n".join(lineas), encoding="utf-8")
        encargo = json.loads((self.a / "ejemplos/encargo.demo.json").read_text())
        encargo["recorridos"] = [
            {"id": q, "objetivo": q, "consulta": q, "superficie": "frontend"}
            for q in ("alfa", "beta")
        ]
        encargo["recorridos_priorizados"] = ["alfa", "beta"]
        path = self.root / "encargo.json"
        path.write_text(json.dumps(encargo))
        reglas = {
            q: {
                "estado": "documentada",
                "detalle": lineas[i],
                "fuentes": [{"path": "manual.md", "locator": q}],
            }
            for q, i in (("alfa", 130), ("beta", 215))
        }
        revision = self.root / "reglas.json"
        revision.write_text(json.dumps(reglas))
        self.cli(
            self.a / "scripts/analizar.py",
            "procesar",
            "--id",
            "piloto",
            "--encargo",
            path,
            "--corpus",
            corpus,
            "--revision",
            revision,
            "--max-chars",
            "5000",
        )
        entrega = json.loads((self.analisis / "reglas.json").read_text())
        for q, i in (("alfa", 130), ("beta", 215)):
            cita = entrega[q]["citas"][0]
            self.assertEqual(cita["start"], cita["end"])
            texto = (self.analisis / "fuentes" / cita["path"]).read_text().splitlines()
            self.assertEqual(texto[cita["start"] - 1], lineas[i])

    def test_app_visible_y_superficies_validadas(self):
        encargo = json.loads((self.a / "ejemplos/encargo.demo.json").read_text())
        encargo.update(app="Mi aplicación de QA", superficies="ambas")
        encargo["recorridos"].append(
            {**encargo["recorridos"][0], "id": "CONS-API", "superficie": "api"}
        )
        entrada = self.root / "encargo.json"
        entrada.write_text(json.dumps(encargo))
        argumentos = ("procesar", "--validar-encargo", "--encargo", entrada)
        salida = self.cli(self.a / "scripts/analizar.py", *argumentos, "--id", "alcance")
        encargo_publicado = json.loads(
            (Path(salida.stdout.strip()) / "encargo.json").read_text()
        )
        self.assertEqual(encargo_publicado["app"], "Mi aplicación de QA")
        self.assertEqual(encargo_publicado["app_id"], "Mi-aplicacion-de-QA")
        self.assertEqual(encargo_publicado["superficies"], ["api", "frontend"])
        encargo["superficies"] = "frontend"
        entrada.write_text(json.dumps(encargo))
        self.cli(self.a / "scripts/analizar.py", *argumentos, "--id", "inconsistente", codigo=2)
        salida = self.cli(
            self.a / "scripts/analizar.py",
            "consolidar", "--id", "alcance", "--id", "inconsistente",
        )
        consolidado = Path(salida.stdout.strip()).read_text()
        self.assertIn("Mi aplicación de QA", consolidado)
        self.assertIn("superficies debe coincidir", consolidado)

    def test_mockup_reproducible_y_referenciado_en_suite(self):
        self.analizar()
        salidas = []
        for identificador in ("mockup-1", "mockup-2"):
            resultado = self.cli(
                self.b / "scripts/mockups.py", "procesar", "--id", identificador,
                "--spec", self.b / "ejemplos/mockup.demo.json", "--nombre", "adjunto",
                "--formato", "docx", "--semilla", 7,
            )
            salidas.append(Path(resultado.stdout.strip()))
        nombre = "fixtures/adjunto.docx"
        original = (salidas[0] / nombre).read_bytes()
        self.assertEqual(original, (salidas[1] / nombre).read_bytes())
        self.diseno["perfil"]["browser_controls"]["adjunto"] = "#input-adjunto"
        self.diseno["casos"][0]["browser_steps"].insert(
            0, {"id": "adjuntar", "type": "upload", "control": "adjunto", "value": "adjunto.docx"}
        )
        self.preparar("--mockups", salidas[0])
        self.assertEqual(original, (self.b / "salidas/casos" / nombre).read_bytes())

    def test_frontend_rechaza_texto_global_como_resultado(self):
        self.analizar()
        self.diseno["casos"][0]["criteria"][0]["check"] = {
            "type": "visible_text", "equals": "en revisión",
        }
        self.assertIn("visible_text", self.preparar(codigo=2).stderr)

    def test_frontend_exige_playwright(self):
        self.analizar()
        self.diseno["pasos"][0]["via"] = "http"
        self.assertIn("frontend requiere", self.preparar(codigo=2).stderr)
        self.assertFalse((self.b / "salidas/casos").exists())

    def test_documentacion_funcional_resuelve_regla_pendiente(self):
        self.revision = self.root / "revision.json"
        self.revision.write_text(
            json.dumps(
                {
                    "CONS-01": {
                        "estado": "pendiente",
                        "detalle": "Confirmar estado y referencia",
                        "fuentes": [],
                    }
                }
            )
        )
        self.analizar(codigo=3)
        guia = self.root / "Guía funcional.md"
        guia.write_text(
            "Trámites\nAl consultar QA-17 la persona ve en revisión y la fuente REG-17.\n"
        )
        self.cli(
            self.b / "scripts/documentacion.py",
            "procesar",
            "--id",
            "contexto",
            "--analisis",
            self.analisis,
            "--documento-funcional",
            guia,
        )
        caso = self.diseno["casos"][0]
        caso["sources"] = [
            {
                "origen": "funcional",
                "path": guia.name,
                "start": 2,
                "end": 2,
                "locator": "REG-17",
            }
        ]
        caso["aclaracion_funcional"] = (
            "La guía precisa el estado y la fuente que ve el usuario."
        )
        self.preparar(codigo=2)
        self.preparar("--contexto-funcional", self.b / "salidas/contexto")
        paquete = self.b / "salidas/casos"
        enviado = json.loads((paquete / "casos.json").read_text())[0]["sources"][0]
        self.assertEqual(enviado["origen"], "funcional")
        self.assertIn("REG-17", (paquete / "fuentes" / enviado["path"]).read_text())
        inventario = json.loads((paquete / "documentacion-funcional.json").read_text())
        self.assertEqual(inventario["extractos"][0]["original"], guia.name)


if __name__ == "__main__":
    unittest.main()
