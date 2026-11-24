"""Transformar el diseño funcional en CSV de QA y un catálogo ejecutable."""

import csv
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from soporte import abrir, citar, huella, principal, read_json, write_json

# isort: split

from azure_export import case_rows, cell
from browser_steps import prepare_steps
from contracts import required_text, string_list, validate_case
from release import inside, load_suite
from runners import checks_for
from session import run_id

CAMPOS = [
    "ID",
    "Tipo de elemento de trabajo",
    "Título",
    "Ruta de área",
    "Asignado a",
    "Estado",
    "Tipo de caso de prueba",
    "Funcionalidad",
    "Tipo de componente",
    "Tipo",
    "Paso",
    "Acción",
    "Resultado esperado",
]
CANALES = {"frontend": {"playwright"}, "api": {"api", "http"}, "db": {"db"}}


def opciones(parser):
    parser.add_argument("--analisis", type=Path, required=True)
    parser.add_argument(
        "--contexto-funcional", type=Path, help="Entrega opcional de documentacion.py"
    )
    parser.add_argument("--diseno", type=Path, required=True)


def exportar(casos, area, ruta):
    titulos, ids = set(), set()
    with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(CAMPOS)
        for c in casos:
            meta = c["azure"]
            titulo = c["title"].strip().casefold()
            if titulo in titulos or len(c["title"].strip()) > 128:
                raise ValueError(f"Título duplicado o demasiado largo: {c['id']}")
            titulos.add(titulo)
            if "work_item_id" in meta:
                if meta["work_item_id"] in ids:
                    raise ValueError("ID de Azure duplicado.")
                ids.add(meta["work_item_id"])
            for fila in case_rows(
                c,
                meta.get("area", area),
                meta.get("assigned_to", ""),
                meta.get("state", "Design"),
            ):
                identificador, _, titulo_qa, paso, accion, esperado, *campos = fila
                writer.writerow(
                    [
                        cell(v)
                        for v in (
                            identificador,
                            "test case",
                            titulo_qa,
                            *campos,
                            paso,
                            accion,
                            esperado,
                        )
                    ]
                )


def operar(args, salida, logs, resumen):
    """Validar el diseño, resolver fuentes y producir ambas representaciones."""
    abrir(args.analisis, "01-analisis", requiere="reglas.json")
    encargo = read_json(args.analisis / "encargo.json")
    analisis = read_json(args.analisis / "analisis.json")
    reglas = read_json(args.analisis / "reglas.json")
    diseno = read_json(args.diseno)
    area = required_text(diseno, "area")
    requisitos = {r["id"]: r for r in encargo["recorridos"]}
    casos, manifiesto = diseno["casos"], diseno["pasos"]
    por_id = {run_id(c["id"]): c for c in casos}
    seleccion = [p["case"] for p in manifiesto]
    if (
        len(por_id) != len(casos)
        or len(set(seleccion)) != len(seleccion)
        or set(seleccion) != set(por_id)
    ):
        raise ValueError(
            "Cada caso diseñado requiere una entrada única en el manifiesto."
        )
    pendientes = diseno.get("pendientes", {})
    cubiertos = {c["requirement"] for c in casos}
    if (
        set(pendientes) != requisitos.keys() - cubiertos
        or cubiertos - requisitos.keys()
        or not all(isinstance(v, str) and v.strip() for v in pendientes.values())
    ):
        raise ValueError(
            "Cada recorrido del encargo requiere casos ejecutables o un motivo explícito en pendientes."
        )
    fuentes = salida / "fuentes"
    shutil.copytree(args.analisis / "fuentes", fuentes)
    shutil.copyfile(args.analisis / "analisis.json", salida / "origen-fuentes.json")
    write_json(salida / "encargo.json", encargo)
    write_json(salida / "reglas.json", reglas)
    funcionales = []
    if args.contexto_funcional:
        abrir(
            args.contexto_funcional, "02-casos", requiere="documentacion-funcional.json"
        )
        contexto = read_json(args.contexto_funcional / "documentacion-funcional.json")
        if contexto["analisis_sha256"] != huella(args.analisis / "entrega.json"):
            raise ValueError(
                "La documentación funcional se consultó para otro análisis."
            )
        funcionales = contexto["extractos"]
        for extracto in funcionales:
            archivo = extracto["archivo"]
            shutil.copyfile(
                inside(args.contexto_funcional / "fuentes", archivo), fuentes / archivo
            )
        write_json(salida / "documentacion-funcional.json", contexto)
        resumen["contexto_funcional_sha256"] = huella(
            args.contexto_funcional / "entrega.json"
        )
    casos_con_fuente_funcional = []
    perfil = diseno["perfil"]
    for p in manifiesto:
        c = por_id[p["case"]]
        validate_case(c)
        string_list(c, "step_expected")
        required_text(c["azure"], "component_type")
        required_text(c["azure"], "test_case_type")
        superficie = requisitos[c["requirement"]]["superficie"]
        if p["via"] not in CANALES[superficie]:
            raise ValueError(
                f"{c['id']}: {superficie} requiere {sorted(CANALES[superficie])}."
            )
        if not c["sources"]:
            raise ValueError(f"{c['id']}: falta citar la regla del análisis.")
        regla = reglas[c["requirement"]]
        citas = []
        for fuente in c["sources"]:
            origen = fuente.get("origen", "segundo_cerebro")
            if origen == "funcional":
                citas.append(citar(fuente, funcionales, fuentes))
            elif origen == "segundo_cerebro":
                cita = citar(fuente, analisis["extractos"], fuentes)
                if not any(
                    cita["path"] == f["path"]
                    and f["start"] <= cita["start"]
                    and cita["end"] <= f["end"]
                    for f in regla["citas"]
                ):
                    raise ValueError(
                        f"{c['id']}: el caso cita fuera de la evidencia de su recorrido."
                    )
                citas.append(cita)
            else:
                raise ValueError(f"{c['id']}: origen documental desconocido.")
        hay_funcional = any(f.get("origen") == "funcional" for f in citas)
        if hay_funcional:
            casos_con_fuente_funcional.append(c["id"])
        if regla["estado"] == "pendiente":
            if not hay_funcional:
                raise ValueError(
                    f"{c['id']}: falta fuente funcional para resolver la duda del análisis."
                )
            required_text(c, "aclaracion_funcional")
        c["sources"] = citas
        recursos = [p["body"]] if "body" in p else []
        for accion in c.get("browser_steps", []):
            if accion["type"] == "upload":
                recursos.append("fixtures/" + accion["value"])
        for recurso in recursos:
            original = inside(args.diseno.resolve().parent, recurso)
            if Path(recurso).parts[:1] != ("fixtures",) or ".." in Path(recurso).parts:
                raise ValueError("Los datos de prueba deben estar bajo fixtures/.")
            destino = salida / recurso
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, destino)
        if superficie == "frontend":
            if c.get("browser_flow") != "web_ui":
                raise ValueError(f"{c['id']}: falta browser_flow=web_ui.")
            # Validación estática. Los valores reales se resuelven solo en el ejecutor.
            variables = {
                a["value_env"]: "dato-de-validacion"
                for a in c.get("browser_steps", [])
                if "value_env" in a
            }
            prepare_steps(
                c, perfil, salida, checks_for(c, "playwright"), environment=variables
            )
    config = {
        "schema": "agentic-qc/suite-1",
        "app": encargo["app"],
        "cases": "casos.json",
        "manifest": "pasos.json",
        "profile": "perfil.json",
        "requirements": "requisitos.json",
        "corpus": "fuentes",
    }
    if "openapi" in diseno:
        contrato = inside(args.diseno.resolve().parent, diseno["openapi"])
        config["openapi"] = "openapi" + contrato.suffix
        shutil.copyfile(contrato, salida / config["openapi"])
    for archivo, valor in (
        ("suite.json", config),
        ("casos.json", casos),
        ("pasos.json", manifiesto),
        ("perfil.json", perfil),
        ("pendientes.json", pendientes),
        ("requisitos.json", list(requisitos)),
    ):
        write_json(salida / archivo, valor)
    if casos:
        load_suite(
            SimpleNamespace(
                suite=salida / "suite.json",
                profile=None,
                corpus=None,
                chrome_visible=False,
            )
        )
    exportar(casos, area, salida / "casos-qa.csv")
    resumen.update(
        analisis_sha256=huella(args.analisis / "entrega.json"),
        diseno_sha256=huella(args.diseno),
        casos=len(casos),
        filas_de_pasos=sum(len(c["steps"]) + bool(c["preconditions"]) for c in casos),
        recorridos_pendientes=pendientes,
        casos_con_fuente_funcional=casos_con_fuente_funcional,
    )
    return 3 if pendientes else 0


if __name__ == "__main__":
    principal(__file__, opciones, operar)
