"""Transformar el diseño funcional en CSV de QA y un catálogo ejecutable."""

from collections import Counter
import csv
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from soporte import abrir, citar, huella, principal, read_json, write_json

# isort: split

from alcance import normalizar
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
    parser.add_argument("--mockups", type=Path, action="append", default=[])
    parser.add_argument("--area-qa", help="Confirmar la ruta de área del CSV")


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


MOTIVOS = {"regla", "fixture", "acceso", "capacidad", "limpieza", "runner", "prioridad", "otro"}


def detalle_pendientes(pendientes):
    resultado = {}
    for clave, dato in pendientes.items():
        if isinstance(dato, str) and dato.strip():
            dato = {"categoria": "otro", "motivo": dato, "siguiente_accion": "Confirmar con QA los requisitos indicados."}
        if not isinstance(dato, dict) or dato.get("categoria") not in MOTIVOS:
            raise ValueError(f"{clave}: pendiente requiere una categoría reconocida.")
        for campo in ("motivo", "siguiente_accion"):
            required_text(dato, campo)
        resultado[clave] = dato
    return resultado


def ruta_area(datos):
    area = required_text(datos, "area").strip()
    if area.casefold() in {"01-analisis", "02-casos", "03-ejecuciones", "v8", "v9"}:
        raise ValueError("area debe ser la ruta de área que QA usa en el CSV.")
    return area


def archivo_fixture(recurso, diseno, mockups):
    ruta = Path(recurso)
    if ruta.is_absolute() or ruta.parts[:1] != ("fixtures",) or ".." in ruta.parts:
        raise ValueError("Los datos de prueba deben estar bajo fixtures/.")
    candidatos = [base for base in (diseno, *mockups) if (base / ruta).is_file()]
    if not candidatos:
        raise ValueError(f"Falta {recurso}. Generá el archivo con mockups.py o adjuntá la fixture de QA.")
    rutas = [inside(base, recurso) for base in candidatos]
    if len({huella(p) for p in rutas}) > 1:
        raise ValueError(f"{recurso} tiene versiones distintas. Elegí una sola.")
    return rutas[0]


def identidad_cita(cita, extracto):
    return (
        extracto["sha256_original"],
        extracto["desde"] + cita["start"] - 1,
        extracto["desde"] + cita["end"] - 1,
    )


def operar(args, salida, logs, resumen):
    """Validar el diseño, resolver fuentes y producir ambas representaciones."""
    abrir(args.analisis, "01-analisis", requiere="reglas.json")
    encargo = normalizar(read_json(args.analisis / "encargo.json"))
    analisis = read_json(args.analisis / "analisis.json")
    reglas = read_json(args.analisis / "reglas.json")
    diseno = read_json(args.diseno)
    area = ruta_area(diseno)
    area_confirmada = args.area_qa or encargo.get("area_qa")
    if area_confirmada and area != area_confirmada.strip():
        raise ValueError("area del diseño no coincide con AREA_QA.")
    for ruta in args.mockups:
        abrir(ruta, "02-casos", requiere="mockup.json")
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
    ):
        raise ValueError(
            "Cada recorrido del encargo requiere casos ejecutables o un motivo explícito en pendientes."
        )
    estructura_pendientes = detalle_pendientes(pendientes)
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
    extractos = {
        e["archivo"]: e for e in [*analisis["extractos"], *funcionales]
    }
    casos_con_fuente_funcional = []
    omitidas = 0
    perfil = diseno["perfil"]
    for p in manifiesto:
        c = por_id[p["case"]]
        validate_case(c)
        string_list(c, "step_expected")
        required_text(c["azure"], "component_type")
        required_text(c["azure"], "test_case_type")
        if "area" in c["azure"]:
            c["azure"]["area"] = ruta_area(c["azure"])
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
        fuentes_unicas = {}
        for cita in citas:
            identidad = identidad_cita(cita, extractos[cita["path"]])
            if identidad in fuentes_unicas:
                omitidas += 1
                if cita.get("origen") != "funcional":
                    continue
            fuentes_unicas[identidad] = cita
        c["sources"] = list(fuentes_unicas.values())
        recursos = [p["body"]] if "body" in p else []
        for accion in c.get("browser_steps", []):
            if accion["type"] == "upload":
                recursos.append("fixtures/" + accion["value"])
        for recurso in recursos:
            original = archivo_fixture(recurso, args.diseno.resolve().parent, args.mockups)
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
            checks = checks_for(c, "playwright")
            if any(check["type"] == "visible_text" for check in checks.values()):
                raise ValueError(f"{c['id']}: usá control_text/control_contains en el resultado de la pantalla. visible_text permite coincidencias fuera del resultado.")
            prepare_steps(c, perfil, salida, checks, environment=variables)
    config = {
        "schema": "agentic-qc/suite-1",
        "app": encargo["app_id"],
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
        ("pendientes.json", {clave: d["motivo"] for clave, d in estructura_pendientes.items()}),
        ("pendientes-detalle.json", estructura_pendientes),
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
        casos_por_superficie=dict(Counter(requisitos[c["requirement"]]["superficie"] for c in casos)),
        area_qa=area,
        areas_csv=sorted({c["azure"].get("area", area) for c in casos}),
        fuentes_duplicadas_omitidas=omitidas,
        filas_de_pasos=sum(len(c["steps"]) + bool(c["preconditions"]) for c in casos),
        recorridos_pendientes=pendientes,
        casos_con_fuente_funcional=casos_con_fuente_funcional,
    )
    return 3 if pendientes else 0


if __name__ == "__main__":
    principal(__file__, opciones, operar)
