"""Controles del contrato entre etapas con archivos y CLI reales."""

import csv
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread

V10 = Path(__file__).resolve().parents[2]

LOGIN = """<!doctype html><form><input id="password" type="password"><button>Entrar</button></form>
<script>document.querySelector('form').onsubmit = async e => {
 e.preventDefault();
 const response = await fetch('/login', {method:'POST',body:document.querySelector('input').value});
 if (response.ok) location.assign('/app');
};</script>"""
APP = """<!doctype html><p id="flag">off</p><form><input id="composer">
<select id="model"><option value="default">Default</option><option value="qa">QA</option></select>
<button id="send">Enviar</button></form>
<section id="history"><article><p class="answer">Resultado de QA</p></article></section>
<button id="export">Descargar</button>
<script>
document.querySelector('form').onsubmit = async e => {
 e.preventDefault();
 const prompt = document.querySelector('#composer').value;
 const response = await fetch('/chat', {method:'POST',body:document.querySelector('#model').value + ':' + prompt});
 const item = document.createElement('article');
 const answer = document.createElement('p');
 answer.className = 'answer';
 answer.textContent = await response.text();
 item.append(answer);
 document.querySelector('#history').append(item);
};
document.querySelector('#export').onclick = () => {
 const link = document.createElement('a');
 link.href = URL.createObjectURL(new Blob(['Informe QA · REG-17'], {type:'text/plain'}));
 link.download = 'informe.txt';
 link.click();
};
</script>"""


class AplicacionQA(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, status, body, *, cookie=False):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if cookie:
            self.send_header("Set-Cookie", "qa_session=session-synthetic; HttpOnly; Path=/")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        if self.path == "/":
            self.send(200, LOGIN)
        elif self.path == "/app":
            authenticated = "qa_session=session-synthetic" in self.headers.get("Cookie", "")
            self.send(200, APP) if authenticated else self.send(401, "Sin sesión")
        elif self.path == "/health":
            self.send(200, "ok")
        else:
            self.send(404, "No existe")

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"])).decode()
        if self.path == "/login":
            self.server.logins += 1
            if body != "clave-ficticia-de-QA":
                self.send(401, "Sin acceso")
            elif self.server.limit:
                self.send(429, "Esperá")
            else:
                self.send(200, "Sesión", cookie=True)
        elif self.path == "/chat":
            authenticated = "qa_session=session-synthetic" in self.headers.get("Cookie", "")
            if not authenticated:
                self.send(401, "Sin sesión")
            elif body == "qa:sonda" or body == "qa:caso" and not self.server.regression:
                self.send(200, "Resultado de QA")
            else:
                self.send(200, "Respuesta distinta")
        else:
            self.send(404, "No existe")


class FlujoV10(unittest.TestCase):
    def setUp(self):
        temporal = TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        self.root = Path(temporal.name)
        self.v10 = self.root / "v10"
        shutil.copytree(
            V10,
            self.v10,
            ignore=shutil.ignore_patterns("logs", "salidas", "credenciales.txt", "__pycache__", "*.zip"),
        )
        self.a = self.v10 / "01-analisis"
        self.b = self.v10 / "02-casos"
        self.c = self.v10 / "03-ejecuciones"
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
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(reader.fieldnames, [
                "ID", "Tipo de elemento de trabajo", "Título", "Ruta de área", "Asignado a", "Estado",
                "Tipo de caso de prueba", "Funcionalidad", "Tipo de componente", "Tipo",
                "Paso", "Acción", "Resultado esperado",
            ])
        csv_bytes = (paquete / "casos-qa.csv").read_bytes()
        self.assertTrue(csv_bytes.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(csv_bytes.count(b"\r\n"), 4)
        self.assertEqual(
            (rows[0]["ID"], rows[0]["Tipo de elemento de trabajo"], rows[0]["Estado"], rows[0]["Tipo"]),
            ("", "test case", "Design", "Functional"),
        )
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
        metrics = json.loads((self.b / "logs/casos/metricas-etapa.json").read_text())
        self.assertEqual((metrics["tokens_entrada_observados"], metrics["tokens_salida_observados"]), (20, 3))
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

    def test_playwright_reutiliza_sesion_y_conserva_retest(self):
        with ThreadingHTTPServer(("127.0.0.1", 0), AplicacionQA) as server:
            server.logins = 0
            server.limit = False
            server.regression = False
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                self.verificar_sesion_y_retest(server)
            finally:
                server.shutdown()

    def test_redaccion_y_lote_de_citas(self):
        form = self.a / "ejemplos/corpus/reglas.md"
        with form.open("a") as stream:
            stream.write('\nservice_password = "credencial-sintetica-no-publicar"\n')
        self.cli(
            self.a / "scripts/analizar.py", "procesar", "--id", "contexto",
            "--encargo", self.a / "ejemplos/encargo.demo.json", "--corpus", form.parent,
            "--conservar-indice",
        )
        root = self.a / "logs/contexto"
        index = next(root.glob("*/navegacion/indice.sqlite"))
        self.assertNotIn(b"credencial-sintetica-no-publicar", index.read_bytes())
        self.assertNotIn("credencial-sintetica-no-publicar", (root / "log01.md").read_text())
        records = json.loads(next(root.glob("*/indice.json")).read_text())
        self.assertEqual(records["redacciones"], [{"path": "reglas.md", "cantidad": 1}])
        self.analizar()
        self.diseno["casos"][0]["sources"] += [
            {"path": "ausente.md", "start": 1, "end": 1},
            {"path": "reglas.md", "start": 500, "end": 501},
            {"path": "reglas.md", "start": 3, "end": 3, "locator": "TEXTO-AUSENTE"},
        ]
        self.preparar(codigo=2)
        report = next((self.b / "logs/casos").glob("*/citas-invalidas.json"))
        self.assertEqual(
            [r["causa"] for r in json.loads(report.read_text())],
            ["archivo_ausente", "rango_ausente", "texto_no_coincide"],
        )

    def test_fixtures_xlsx_y_pdf_son_reproducibles(self):
        for fmt in ("xlsx", "pdf"):
            outputs = []
            for index in range(2):
                identifier = f"fixture-{fmt}-{index}"
                self.cli(
                    self.b / "scripts/mockups.py", "procesar", "--id", identifier,
                    "--nombre", "datos", "--formato", fmt, "--cantidad", 3, "--semilla", 42,
                    "--spec", self.b / "ejemplos/mockup.demo.json",
                )
                outputs.append(json.loads((self.b / "salidas" / identifier / "mockup.json").read_text()))
            self.assertEqual(outputs[0], outputs[1])
            expected = {"hojas": 1, "filas_datos": 3, "columnas": 3} if fmt == "xlsx" else {"paginas": 1}
            self.assertEqual(outputs[0]["estructura"], expected)

    def verificar_sesion_y_retest(self, server):
        profile = self.diseno["perfil"]
        profile["base_url"] = f"http://127.0.0.1:{server.server_port}"
        profile["timeout_seconds"] = 2
        profile["http_operations"] = [
            {"method": "POST", "path": "/login"},
            {"method": "POST", "path": "/chat"},
            {"method": "GET", "path": "/health"},
        ]
        profile["browser_paths"] = ["/", "/app"]
        profile["browser_controls"] = {
            "password": "#password", "login": "button", "composer": "#composer", "model": "#model",
            "send": "#send", "turn": "#history > article", "answer": ".answer", "flag": "#flag",
            "file": "#export",
        }

        def chat_steps(question):
            return [
                {"id": "select", "type": "select", "control": "model", "value": "qa"},
                {"id": "verify", "type": "verify_model", "control": "model", "property": "value", "value": "qa"},
                {"id": "before", "type": "capture_count", "control": "turn"},
                {"id": "question", "type": "fill", "control": "composer", "value": question},
                {"id": "send", "type": "click", "control": "send"},
            ]

        answer = [{
            "id": "answer", "expected": "Resultado de QA",
            "check": {"type": "control_text", "control": "answer", "scope": "before", "equals": "Resultado de QA"},
        }]
        profile["browser_setups"] = {"qa": {
            "actor": "qa", "browser_path": "/", "ready_control": "composer", "timeout_seconds": 3,
            "login": {"step": "sign-in", "method": "POST", "path": "/login"},
            "browser_steps": [
                {"id": "password", "type": "fill", "control": "password", "value_env": "QA_TEST_DEMO_PASS"},
                {"id": "sign-in", "type": "click", "control": "login"},
            ],
            "probe": {"browser_steps": chat_steps("sonda"), "criteria": answer},
        }}
        chat = self.diseno["casos"][0]
        chat.update(
            browser_path="/app", browser_setup="qa", criteria=answer,
            browser_steps=chat_steps("caso"), browser_preconditions=[{"control": "flag", "equals": "off"}],
            browser_model={"value": "qa", "before": "question"},
        )
        download = deepcopy(chat)
        del download["browser_model"]
        download.update(
            id="UI-FILE", title="Exportar un informe TXT",
            browser_steps=[{"id": "export", "type": "download", "control": "file"}],
            criteria=[{"id": "export", "expected": "Incluye el dato funcional", "check": {
                "type": "download_file", "step": "export", "extension": ".txt", "contains": ["REG-17"],
            }}],
            variante={"grupo": "exportacion", "formato": "txt", "tipo": "descarga"},
        )
        encargo_path = self.a / "ejemplos/encargo.demo.json"
        encargo = json.loads(encargo_path.read_text())
        encargo.update(superficies="ambas")
        encargo["recorridos"].append({
            **encargo["recorridos"][0], "id": "API-01", "superficie": "api",
        })
        encargo_path.write_text(json.dumps(encargo))
        revision = json.loads(self.revision.read_text())
        revision["API-01"] = revision["CONS-01"]
        self.revision.write_text(json.dumps(revision))
        health = {
            key: deepcopy(value) for key, value in chat.items()
            if not key.startswith("browser_")
        }
        health.update(
            id="API-HEALTH", title="Consultar disponibilidad", requirement="API-01",
            http={"method": "GET", "path": "/health"},
            criteria=[{"id": "health", "expected": "HTTP 200", "check": {"type": "status", "equals": 200}}],
        )
        after = {**health, "id": "API-DEP", "title": "Consultar disponibilidad después de exportación"}
        self.diseno["casos"] += [download, health, after]
        self.diseno["pasos"] += [
            {"case": "UI-FILE", "via": "playwright"},
            {"case": "API-HEALTH", "via": "http"},
            {"case": "API-DEP", "via": "http", "depends_on": ["UI-FILE"]},
        ]
        self.analizar()
        self.preparar()
        credenciales = self.root / "credenciales.txt"
        credenciales.write_text("QA_TEST_DEMO_PASS=clave-ficticia-de-QA\n")
        credenciales.chmod(0o600)

        def ejecutar(identifier, code):
            self.cli(
                self.c / "scripts/ejecutar.py", "procesar", "--id", identifier,
                "--casos", self.b / "salidas/casos", "--credenciales", credenciales, codigo=code,
            )
            return json.loads((self.c / f"salidas/{identifier}/dictamen.json").read_text())

        antes = ejecutar("antes", 0)
        self.assertEqual(antes["casos_ui_aprobados"], ["CHAT-UI", "UI-FILE"])
        self.assertEqual(server.logins, 1)
        server.regression = True
        degradada = ejecutar("degradada", 1)
        estados = {r["case"]: r["status"] for r in degradada["casos"]}
        self.assertEqual(estados["CHAT-UI"], "failed", "La coincidencia del mensaje histórico no debe pasar.")
        self.assertEqual(estados["UI-FILE"], "passed")
        server.limit = True
        retest = ejecutar("retest", 3)
        login = retest["preflight"]["grupos_funcionales"]["qa"]["login"]
        self.assertEqual(login, {"method": "POST", "path": "/login", "status": 429})
        self.assertEqual(server.logins, 3)
        self.assertEqual(retest["intentos"], 1)
        self.assertEqual(retest["casos_sin_ejecutar"], ["CHAT-UI", "UI-FILE", "API-DEP"])
        log = (self.c / "logs/retest/log03.md").read_text()
        self.assertNotIn("clave-ficticia-de-QA", log)
        self.assertNotIn("session-synthetic", log)
        manual = self.root / "manual.json"
        manual.write_text(json.dumps({"CHAT-UI": {
            "decision": "aceptado", "responsable": "QA", "motivo": "Observación adicional", "evidencia": "ACTA-DEMO",
        }}))
        result = self.cli(
            self.c / "scripts/historial_retest.py", "--anterior", self.c / "salidas/degradada",
            "--actual", self.c / "salidas/retest", "--disposicion", manual,
        )
        fila = json.loads(Path(result.stdout.strip()).read_text())["casos"]["CHAT-UI"]
        self.assertEqual(fila["anterior_automatico"]["estado"], "failed")
        self.assertEqual(fila["actual_automatico"]["estado"], "unattempted")
        self.assertEqual(fila["decision_manual"]["decision"], "aceptado")

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
