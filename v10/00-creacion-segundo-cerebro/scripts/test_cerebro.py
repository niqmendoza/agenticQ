"""Integración de la etapa 00 con commits locales y la entrega consumida por 01."""

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

V10 = Path(__file__).resolve().parents[2]


class CrearSegundoCerebro(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.v10 = self.root / "v10"
        shutil.copytree(V10, self.v10, ignore=shutil.ignore_patterns(
            ".git", "logs", "salidas", "credenciales.txt", "__pycache__", "*.zip",
        ))
        self.stage = self.v10 / "00-creacion-segundo-cerebro"
        self.repo = self.root / "app"
        self.repo.mkdir()
        self.git("init", "-q")
        self.poner("api/tramites.py", "def consultar():\n    return 'QA-17 está en revisión y cita REG-17'\n")
        self.poner("web/pantalla.ts", 'export function mostrar() { return "Estado"; }\n')
        self.poner("reportes/exportar.go", 'func Exportar() string { return "CSV"; }\n')
        self.poner(".env", "QA_PRIVATE=secreto-de-archivo-omitido\n")
        self.poner("api/config.py", 'service_password = "credencial-ficticia-indice"\n')
        self.poner("node_modules/paquete/index.js", "texto que no se indexa\n")
        self.commit("base")
        self.config = self.root / "modulos.json"
        self.config.write_text(json.dumps({
            "api": {"prefijos": ["api"]},
            "web": {"prefijos": ["web"], "depende_de": ["api"]},
            "reportes": {"prefijos": ["reportes"]},
        }))

    def poner(self, path, text):
        file = self.repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")

    def git(self, *args):
        response = subprocess.run(["git", "-C", str(self.repo), *args], capture_output=True, text=True)
        self.assertEqual(response.returncode, 0, response.stderr)
        return response.stdout.strip()

    def commit(self, name):
        self.git("add", ".")
        self.git("-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-qm", name)
        return self.git("rev-parse", "HEAD")

    def cli(self, script, *args, code=0):
        result = subprocess.run(
            [sys.executable, str(script), *map(str, args)], cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def hacer(self, script, name, *args, code=0):
        self.cli(self.stage / "scripts" / f"{script}.py", "procesar", "--id", name, *args, code=code)
        return self.stage / "salidas" / name

    def mapear(self, name, *extra):
        return self.hacer("mapear", name, "--repo", self.repo, "--app", "Chat de trámites",
                          "--modulos", self.config, *extra)

    def ficha(self, module, path, line, marker, claim, *, relaciones=None):
        key = self.root / (module + ".json")
        key.write_text(json.dumps({
            "modulo": module, "pendientes": [], "hechos": [{
                "id": "hecho", "tipo": "regla", "titulo": "Resultado esperado",
                "afirmacion": claim,
                "evidencia": [{"archivo": path, "desde": line, "hasta": line, "localizador": marker}],
                **({"relaciones": relaciones} if relaciones is not None else {}),
            }],
        }))
        return key

    def test_mapear_publicar_y_consumir_con_presupuesto(self):
        commit = self.git("rev-parse", "HEAD")
        self.poner("api/tramites.py", "cambio sin confirmar\n")
        mapa = self.mapear("inventario")
        info = json.loads((mapa / "mapa.json").read_text())
        self.assertEqual(info["commit"], commit)
        self.assertEqual(info["archivos_indexados"], 4)
        self.assertEqual(info["redacciones"], 1)
        self.assertEqual(info["omisiones"]["archivo_sensible"], 1)
        with closing(sqlite3.connect(mapa / "indice.sqlite")) as db:
            text = "\n".join(row[0] for row in db.execute("SELECT texto FROM archivos"))
            self.assertIn("REG-17", text)
            self.assertNotIn("cambio sin confirmar", text)
            self.assertNotIn("credencial-ficticia-indice", text)
        vista = self.hacer("navegar", "busqueda", "--mapa", mapa, "--modulo", "api",
                           "--consulta", "QA-17 REG-17 revisión", "--max-chars", 800)
        context = (vista / "contexto.json").read_text()
        self.assertLessEqual(len(context), 800)
        self.assertIn("REG-17", json.loads(context)["entradas"][0]["texto"])
        with_cita = self.ficha(
            "api", "api/tramites.py", 2, "QA-17 está en revisión",
            "El trámite QA-17 está en revisión y la respuesta cita REG-17.",
            relaciones=[{"tipo": "relacionado con", "destino": "web/hecho"}],
        )
        brain = self.hacer("publicar", "cerebro", "--por-modulo", "--mapa", mapa, "--revision", with_cita, code=3)
        self.assertFalse((brain / "indice.sqlite").exists())
        bundle = brain / "corpus"
        self.assertEqual(yaml.safe_load((bundle / "index.md").read_text().split("---")[1]), {"okf_version": "0.2"})
        self.assertFalse((bundle / "modulos/api/index.md").read_text().startswith("---"))
        for doc in bundle.rglob("*.md"):
            if doc.name not in {"index.md", "log.md"}:
                self.assertTrue(yaml.safe_load(doc.read_text().split("---")[1])["type"])
        fact_file = bundle / "modulos/api/concepto-hecho.md"
        fact_text = fact_file.read_text()
        meta = yaml.safe_load(fact_text.split("---")[1])
        self.assertEqual(meta["type"], "Regla funcional")
        self.assertEqual(meta["status"], "draft")
        self.assertNotIn("verified", meta)
        self.assertIn(commit, meta["sources"][0]["resource"])
        self.assertIn("[^" + meta["sources"][0]["id"] + "]", fact_text)
        pending = json.loads((brain / "manifiesto.json").read_text())["relaciones_pendientes"]
        self.assertEqual(pending[0]["destino"], "web/hecho")
        stage1 = self.v10 / "01-analisis"
        revision = self.root / "revision.json"
        revision.write_text(json.dumps({
            "CONS-01": {"estado": "documentada", "detalle": "QA-17 está en revisión.",
                        "fuentes": [{"path": "modulos/api/concepto-hecho.md", "locator": "El trámite QA-17 está en revisión"}]},
        }))
        self.cli(
            stage1 / "scripts/analizar.py", "procesar", "--id", "analisis",
            "--cerebro", brain, "--encargo", stage1 / "ejemplos/encargo.demo.json", "--revision", revision,
            "--conservar-indice",
        )
        analysis = json.loads((stage1 / "salidas/analisis/analisis.json").read_text())
        self.assertEqual(analysis["cerebro_origen"]["commit"], commit)
        self.assertEqual(analysis["cerebro_origen"]["okf_version"], "0.2")
        self.assertTrue((stage1 / "salidas/analisis/reglas.json").is_file())
        index = next((stage1 / "logs/analisis").glob("*/navegacion/indice.sqlite"))
        with closing(sqlite3.connect(index)) as db:
            edges = set(db.execute("SELECT source, target FROM edges"))
            self.assertIn(("index.md", "modulos/index.md"), edges)
            self.assertIn(("modulos/web/modulo.md", "modulos/api/modulo.md"), edges)
            self.assertIn(("modulos/api/modulo.md", "modulos/api/concepto-hecho.md"), edges)
        self.cli(self.stage / "scripts/publicar.py", "consolidar", "--id", "inventario", "--id", "busqueda", "--id", "cerebro")
        consolidated = (self.stage / "logs/log00.md").read_text()
        self.assertIn("caracteres_contexto", consolidated)
        self.assertNotIn("credencial-ficticia-indice", consolidated)

    def test_citas_e_incremental_revisan_dependientes(self):
        mapa = self.mapear("inicial")
        invalid = self.ficha("api", "api/tramites.py", 1, "REG-17", "Cita incorrecta")
        self.hacer("publicar", "invalido", "--por-modulo", "--mapa", mapa, "--revision", invalid, code=2)
        api = self.ficha("api", "api/tramites.py", 2, "QA-17", "El trámite QA-17 está en revisión.")
        web = self.ficha(
            "web", "web/pantalla.ts", 1, "Estado", "La pantalla muestra el estado.",
            relaciones=[{"tipo": "usa", "destino": "api/hecho"}],
        )
        reports = self.ficha("reportes", "reportes/exportar.go", 1, "CSV", "El módulo emite CSV.")
        old = self.hacer("publicar", "anterior", "--por-modulo", "--mapa", mapa, "--revision", api, "--revision", web, "--revision", reports)
        self.assertIn("[Resultado esperado](/modulos/api/concepto-hecho.md)",
                      (old / "corpus/modulos/web/concepto-hecho.md").read_text())
        self.poner("api/tramites.py", "def consultar():\n    return 'QA-17 aprobado'\n")
        self.commit("cambio local")
        nuevo = self.mapear("nuevo", "--anterior", old)
        modules = json.loads((nuevo / "mapa.json").read_text())["modulos"]
        self.assertEqual({key: value["revision"] for key, value in modules.items()},
                         {"api": "pendiente", "web": "pendiente", "reportes": "reutilizable"})
        actual = self.hacer("publicar", "actual", "--por-modulo", "--mapa", nuevo, "--anterior", old, code=3)
        manifest = json.loads((actual / "manifiesto.json").read_text())
        self.assertEqual(manifest["modulos"]["reportes"]["estado"], "reutilizado")
        self.assertEqual(manifest["hechos"], 1)

    def test_diagnostico_reune_cortes_y_busquedas_sin_copiar_telemetria(self):
        mapa = self.mapear("piloto-mapa")
        for suffix in ("uno", "dos"):
            self.hacer("navegar", f"piloto-busqueda-{suffix}", "--mapa", mapa,
                       "--consulta", "QA-17 revisión", "--modulo", "api", "--max-chars", 900)
        api = self.ficha("api", "api/tramites.py", 2, "REG-17", "El trámite QA-17 está en revisión y cita REG-17.")
        bundle = self.hacer("publicar", "piloto-publicar", "--por-modulo", "--mapa", mapa, "--revision", api, code=3)
        meter = self.stage / "scripts/publicar.py"
        telemetry = self.root / "otel.jsonl"
        spans = []
        for index, tokens in enumerate(((100, 12), (120, 18))):
            spans.append({
                "startTime": f"2026-11-19T12:00:0{index}Z", "endTime": f"2026-11-19T12:00:0{index + 1}Z",
                "traceId": "traza-sintetica", "spanId": f"llamada-{index}",
                "attributes": {
                    "gen_ai.operation.name": "chat", "gen_ai.conversation.id": "sesion-unica-sintetica",
                    "gen_ai.usage.input_tokens": tokens[0], "gen_ai.usage.output_tokens": tokens[1],
                    "gen_ai.usage.cache_read.input_tokens": 40 + index,
                    "gen_ai.response.model": "modelo-sintetico",
                    "gen_ai.input.messages": "texto de telemetria que no debe ir al diagnostico",
                },
            })
        telemetry.write_text(json.dumps(spans[0]) + "\n")
        self.cli(meter, "medir", "--id", "piloto-mapa", "--archivo", telemetry)
        telemetry.write_text("\n".join(json.dumps(span) for span in [*spans, spans[-1]]) + "\n")
        self.cli(meter, "medir", "--id", "piloto-publicar", "--archivo", telemetry)
        probes = self.root / "pruebas.json"
        rows = [{
            "id": "estado", "consulta": "QA-17 revisión", "concepto": "api/hecho", "localizador": "REG-17",
        }]
        probes.write_text(json.dumps(rows))
        result = self.hacer("diagnosticar", "piloto-diagnostico", "--cerebro", bundle, "--corrida", "piloto",
                            "--pruebas", probes)
        raw = (result / "diagnostico.json").read_text()
        report = json.loads(raw)
        self.assertEqual(report["consumo"]["tokens_total"], 250)
        self.assertEqual(report["consumo"]["tokens_cache_lectura"], 81)
        self.assertEqual(report["consumo"]["llamadas_observadas"], 2)
        self.assertEqual(report["consumo"]["conversaciones_medidas"], 1)
        self.assertEqual(report["consumo"]["por_modelo"]["modelo-sintetico"]["tokens_entrada"], 220)
        self.assertEqual(report["navegacion"]["contextos_verificados"], 2)
        self.assertGreater(report["navegacion"]["fragmentos_exactos_repetidos"], 0)
        self.assertEqual(report["okf"]["incidencias"], [])
        self.assertEqual(report["recuperacion"]["casos"][0]["en_lote"]["estado"], "recuperado")
        self.assertNotIn("texto de telemetria", raw)
        self.assertNotIn("sesion-unica-sintetica", raw)
        copia = self.hacer("publicar", "republicado", "--por-modulo", "--mapa", mapa, "--revision", api, code=3)
        revision = self.hacer("diagnosticar", "sin-medicion", "--cerebro", copia, "--pruebas", probes)
        sin_medicion = json.loads((revision / "diagnostico.json").read_text())
        self.assertEqual(sin_medicion["consumo"]["estado"], "sin_medicion")
        self.assertIsNone(sin_medicion["consumo"]["tokens_total"])
        self.assertEqual(sin_medicion["corpus_sha256"], report["corpus_sha256"])
        rows[0]["concepto"] = "api/ausente"
        probes.write_text(json.dumps(rows))
        ausente = self.hacer("diagnosticar", "fallo-diagnostico", "--cerebro", bundle,
                             "--pruebas", probes, code=3)
        self.assertEqual(json.loads((ausente / "diagnostico.json").read_text())
                         ["recuperacion"]["casos"][0]["en_lote"]["estado"], "concepto_ausente")

    def publicar_demo_tematico(self, nombre, *, codigo=0, cambiar_taxonomia=None):
        mapa = self.hacer("mapear", f"mapa-{nombre}", "--repo", self.stage / "ejemplos/repositorio-demo",
                          "--app", "Aplicación de trámites")
        tax = self.stage / "ejemplos/taxonomia.demo.json"
        if cambiar_taxonomia:
            datos = json.loads(tax.read_text())
            cambiar_taxonomia(datos)
            tax = self.root / "taxonomia-editada.json"
            tax.write_text(json.dumps(datos))
        return self.hacer("publicar", nombre, "--mapa", mapa, "--taxonomia", tax,
                           "--revision", self.stage / "ejemplos/ficha.demo.json", code=codigo)

    def demo_en_git(self):
        repo = self.stage / "ejemplos/repositorio-demo"
        for command in (
            ["init", "-q"], ["add", "."],
            ["-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-qm", "demo"],
        ):
            subprocess.run(["git", "-C", str(repo), *command], check=True, capture_output=True)

    def test_grafo_tematico_consumido_por_01_y_exportado_sin_tocar_notas(self):
        self.demo_en_git()
        entrega = self.publicar_demo_tematico("tematico")
        corpus = entrega / "corpus"
        hecho = "temas/consultas/concepto-consulta-estado.md"
        relacion = "../trazabilidad/concepto-referencia-tramite.md"
        self.assertIn(relacion, (corpus / hecho).read_text())
        self.assertIn("REG-17 es la referencia", (corpus / hecho).read_text())
        self.assertIn("Referenciado por", (corpus / "temas/trazabilidad/concepto-referencia-tramite.md").read_text())
        self.assertEqual((corpus / "index.md").read_text().count(hecho), 1)
        self.assertTrue((corpus / "mocs/respuesta-tramites.md").is_file())
        salida = self.hacer("diagnosticar", "diagnostico-tematico", "--cerebro", entrega)
        informe = json.loads((salida / "diagnostico.json").read_text())
        grafo = informe["okf"]["grafo_tematico"]
        self.assertEqual(grafo["indice_raiz_unico"], 2)
        self.assertEqual(grafo["relaciones_justificadas"], 1)
        self.assertEqual(grafo["relaciones_entre_areas"], 1)
        self.assertEqual(grafo["conceptos_aislados"], [])
        self.assertEqual(informe["recuperacion"]["recuperadas_en_lote"], 2)

        stage1 = self.v10 / "01-analisis"
        self.cli(stage1 / "scripts/analizar.py", "procesar", "--id", "analisis-tematico",
                 "--cerebro", entrega, "--encargo", stage1 / "ejemplos/encargo.demo.json")
        analisis = json.loads((stage1 / "salidas/analisis-tematico/analisis.json").read_text())
        self.assertIn(hecho, {x["original"] for x in analisis["extractos"]})

        nota = self.root / "vault anterior/Inicio.md"
        nota.parent.mkdir()
        nota.write_text("# Referencia anterior\n")
        nueva = self.root / "vault nueva"
        script = self.stage / "scripts/exportar_vault.py"
        self.cli(script, "--cerebro", entrega, "--destino", nueva, "--referencia", "Guía anterior", nota)
        self.cli(script, "--cerebro", entrega, "--destino", nueva, code=2)
        self.assertEqual(nota.read_text(), "# Referencia anterior\n")
        self.assertIn("../vault%20anterior/Inicio.md", (nueva / "index.md").read_text())
        self.assertNotIn("Notas preexistentes", (corpus / "index.md").read_text())

        ruta = corpus / "index.md"
        original = ruta.read_text()
        duplicado = next(line for line in original.splitlines() if f"({hecho})" in line)
        ruta.write_text(original + "\n" + duplicado + "\n")
        receipt = entrega / "entrega.json"
        dato = json.loads(receipt.read_text())
        dato["archivos"]["corpus/index.md"] = hashlib.sha256(ruta.read_bytes()).hexdigest()
        receipt.write_text(json.dumps(dato))
        alterado = self.hacer("diagnosticar", "diagnostico-duplicado", "--cerebro", entrega, code=3)
        estado = json.loads((alterado / "diagnostico.json").read_text())
        self.assertIn("indice_raiz_incorrecto", {x["causa"] for x in estado["okf"]["incidencias"]})

    def test_rechaza_conceptos_sin_area_o_borradores_por_defecto(self):
        self.demo_en_git()
        def duplicar(datos):
            datos["areas"][1]["conceptos"].append("api/consulta-estado")
            datos["mocs"][0]["conceptos"][0]["destino"] = "api/ausente"
        self.publicar_demo_tematico("invalido-tematico", codigo=2, cambiar_taxonomia=duplicar)
        logs = next((self.stage / "logs/invalido-tematico").glob("*/validacion-grafo.json"))
        self.assertEqual({x["causa"] for x in json.loads(logs.read_text())["incidencias"]},
                         {"pertenencia_incorrecta", "concepto_ausente_en_moc"})
        self.hacer("publicar", "borrador", "--mapa", self.stage / "salidas/mapa-invalido-tematico", code=2)

    def test_v3_recupera_escenarios_y_bloquea_revision_con_fuente_modificada(self):
        self.demo_en_git()
        samples = self.stage / "ejemplos"
        profile = samples / "perfil-qc.demo.json"
        mapa = self.hacer("mapear", "mapa-qc", "--perfil", profile)
        info = json.loads((mapa / "mapa.json").read_text())
        raw = json.loads((samples / "fichas-qc.demo.json").read_text())
        raw[0]["revision"] = {"estado": "listo-para-qc", "por": "QA sintético", "commit": info["commit"]}
        fichas = self.root / "fichas-qc.json"
        fichas.write_text(json.dumps(raw))
        migracion = self.root / "migracion.json"
        migracion.write_text(json.dumps([
            {"nota": "vault anterior/Regla.md", "decision": "incorporada", "destino": "consulta-tramite/valido-registro",
             "motivo": "El caso ahora cita el contrato del commit."}
        ]))
        args = ["--taxonomia", samples / "taxonomia.demo.json", "--revision", samples / "ficha.demo.json"]
        incompleta = self.root / "qc-sin-fallo.json"
        incompleta.write_text(json.dumps([{**raw[0], "escenarios": raw[0]["escenarios"][:1]}]))
        self.hacer("publicar", "promocion-invalida", "--mapa", mapa, *args, "--fichas-qc", incompleta, code=2)
        entrega = self.hacer("publicar", "v3", "--mapa", mapa, *args, "--fichas-qc", fichas, "--migracion", migracion)
        replay = self.hacer("publicar", "v3-republicado", "--mapa", mapa, *args, "--anterior", entrega)
        self.assertIn("qc/consulta-tramite.md", (entrega / "corpus/inicio.md").read_text())
        self.assertEqual(json.loads((entrega / "migracion.json").read_text())[0]["decision"], "incorporada")
        recuperado = self.hacer("recuperar_qc", "escenario-qc", "--cerebro", entrega, "--mapa", mapa,
                               "--flujo", "consulta-tramite", "--caso", "fallo-ausente")
        contexto = json.loads((recuperado / "contexto-qc.json").read_text())
        self.assertEqual(contexto["ejecucion"], "no-ejecutado")
        self.assertIn("HTTP 404", contexto["evidencia"][0]["texto"])
        self.assertNotIn("## Caso valido-registro", contexto["ficha"]["texto"])
        piloto = self.hacer("piloto_qc", "piloto-v3", "--cerebro", entrega, "--mapa", mapa,
                           "--consultas", samples / "consultas-qc.demo.json", "--republicacion", replay, code=3)
        informe = json.loads((piloto / "piloto-qc.json").read_text())
        self.assertTrue(informe["controles"]["integridad"])
        self.assertTrue(informe["controles"]["republicacion_identica"])
        self.assertTrue(informe["controles"]["recuperacion"], informe["recuperacion"])
        self.assertIsNone(informe["controles"]["corte_nativo"])
        self.assertIsNone(informe["controles"]["utilidad_revisada"])

        stage1 = self.v10 / "01-analisis"
        encargo = json.loads((stage1 / "ejemplos/encargo.demo.json").read_text())
        encargo["recorridos"][0]["consulta"] = "fallo-ausente HTTP 404 para trámite desconocido"
        enc = self.root / "encargo.json"
        enc.write_text(json.dumps(encargo))
        self.cli(stage1 / "scripts/analizar.py", "procesar", "--id", "analisis-qc",
                 "--cerebro", entrega, "--encargo", enc)
        analisis = json.loads((stage1 / "salidas/analisis-qc/analisis.json").read_text())
        self.assertIn("qc/consulta-tramite.md", {x["original"] for x in analisis["extractos"]})

        repos = samples / "repositorio-demo"
        with (repos / "api/contrato.md").open("a") as stream:
            stream.write("\nSe actualizó el contrato.\n")
        for cmd in (["add", "."], ["-c", "user.email=qa@example.test", "-c", "user.name=QA", "commit", "-qm", "cambio"]):
            subprocess.run(["git", "-C", str(repos), *cmd], check=True, capture_output=True)
        nuevo_mapa = self.hacer("mapear", "mapa-qc-cambio", "--perfil", profile, "--anterior", entrega)
        nueva = self.hacer("publicar", "v3-bloqueado", "--mapa", nuevo_mapa, *args, "--anterior", entrega, code=3)
        cambiada = json.loads((nueva / "fichas-qc.json").read_text())["consulta-tramite"]
        self.assertEqual(cambiada["revision"]["estado"], "bloqueado")
        self.assertTrue(cambiada["invalidaciones"])
        self.assertFalse(cambiada["escenarios"][0]["evidencia"])
