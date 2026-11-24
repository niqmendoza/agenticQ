"""Ejecutar exclusivamente el catálogo entregado por diseño y conservar el dictamen."""

import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from rutas import EJECUCIONES
from soporte import abrir, huella, principal, read_json, write_json

# isort: split

from runners import Unavailable, playwright_browser, profile_for_run


def opciones(parser):
    parser.add_argument("--casos", required=True, type=Path)
    parser.add_argument("--chrome-visible", action="store_true")
    parser.add_argument(
        "--build", help="Repetir la misma suite sobre otro build del mismo entorno"
    )


def operar(args, salida, logs, resumen):
    """Comprobar dependencias y ejecutar el manifiesto con el runner de QA."""
    carpeta = args.casos.resolve()
    abrir(carpeta, "02-casos", requiere="suite.json")
    encargo = read_json(carpeta / "encargo.json")
    casos = read_json(carpeta / "casos.json")
    pendientes = read_json(carpeta / "pendientes.json")
    web = [c for c in casos if c.get("browser_flow") == "web_ui"]
    build = args.build or encargo["build"]
    perfil = profile_for_run(
        read_json(carpeta / "perfil.json"), chrome_visible=args.chrome_visible
    )
    preflight = {
        "interprete": sys.executable,
        "navegador_requerido": bool(web),
        "navegador": "no solicitado",
        "variables_ausentes": [],
    }
    if web:
        try:
            with playwright_browser(perfil):
                preflight["navegador"] = "iniciado"
        except (Unavailable, OSError) as exc:
            preflight["navegador"] = "bloqueado"
            preflight["motivo"] = str(exc)
        variables = {
            a["value_env"] for c in web for a in c["browser_steps"] if "value_env" in a
        }
        preflight["variables_ausentes"] = sorted(
            v for v in variables if not os.environ.get(v)
        )
    write_json(logs / "preflight.json", preflight)
    informe = {
        "app": encargo["app"],
        "entorno": encargo["entorno"],
        "build": build,
        "diseno_sha256": huella(carpeta / "entrega.json"),
        "recorridos_solicitados": encargo["recorridos"],
        "casos_ejecutables": len(casos),
        "casos_ui_planificados": [c["id"] for c in web],
        "casos_ui_con_interaccion_observada": [],
        "casos_ui_aprobados": [],
        "pendientes_de_diseno": pendientes,
        "preflight": preflight,
    }
    if (
        not casos
        or preflight["navegador"] == "bloqueado"
        or preflight["variables_ausentes"]
    ):
        informe.update(
            dictamen="inconclusa",
            intentos=0,
            motivo="Faltan prerrequisitos de la corrida o casos ejecutables.",
            casos_sin_ejecutar=[c["id"] for c in casos],
        )
        codigo = 3
    else:
        trabajo = logs / "motor"
        cmd = [
            sys.executable,
            str(EJECUCIONES / "qa.py"),
            "run",
            "--suite",
            str(carpeta / "suite.json"),
            "--build",
            build,
            "--env",
            encargo["entorno"],
            "--id",
            args.id,
        ]
        if args.chrome_visible:
            cmd.append("--chrome-visible")
        with (logs / "runner.log").open("w", encoding="utf-8") as log:
            proceso = subprocess.run(
                cmd,
                check=False,
                stdout=log,
                stderr=subprocess.STDOUT,
                env={**os.environ, "QC_WORKSPACE": str(trabajo)},
            )
        codigo = proceso.returncode
        resultado = trabajo / "resultados" / args.id
        if codigo not in (0, 1, 3) or not (resultado / "resultado.json").is_file():
            raise ValueError(
                "El runner no produjo un dictamen válido. Revisá runner.log."
            )
        shutil.copytree(resultado, salida / "resultados")
        shutil.copyfile(resultado.with_suffix(".zip"), salida / "resultados.zip")
        datos = read_json(resultado / "resultado.json")
        eventos = read_json(trabajo / ".trabajo" / args.id / "events.json")
        intentos = [e for e in eventos if e["kind"] == "execution"]
        observados = {
            e["case_id"]
            for e in intentos
            if e["execution_method"] == "playwright"
            and any(p["outcome"] == "observed" for p in e.get("browser_steps", []))
        }
        informe["casos_ui_con_interaccion_observada"] = [
            c["id"] for c in web if c["id"] in observados
        ]
        por_id = {r["case"]: r for r in datos["cases"]}
        informe["casos_ui_aprobados"] = [
            i
            for i in informe["casos_ui_con_interaccion_observada"]
            if por_id[i]["status"] == "passed"
        ]
        for row in datos["cases"]:
            if row["evidence"]:
                row["evidence"] = "resultados/" + row["evidence"]
        informe.update(
            dictamen=datos["decision"],
            intentos=len(intentos),
            estados=dict(Counter(r["status"] for r in datos["cases"])),
            casos=datos["cases"],
            resultados="resultados/resultado.json",
        )
    # Vincular la pregunta de QA con los casos y su evidencia también al bloquearse el preflight.
    por_caso = {r["case"]: r for r in informe.get("casos", [])}
    cobertura = {}
    for recorrido in encargo["recorridos"]:
        clave = recorrido["id"]
        seleccion = [c["id"] for c in casos if c["requirement"] == clave]
        estados = {por_caso[c]["status"] for c in seleccion if c in por_caso}
        if "failed" in estados:
            estado = "fallido"
        elif estados == {"passed"} and all(c in por_caso for c in seleccion):
            estado = "aprobado"
        else:
            estado = "pendiente" if clave in pendientes else "inconcluso"
        cobertura[clave] = {
            "estado": estado,
            "casos": seleccion,
            "evidencias": [
                por_caso[c]["evidence"]
                for c in seleccion
                if c in por_caso and por_caso[c]["evidence"]
            ],
        }
    informe["cobertura_por_recorrido"] = cobertura
    write_json(salida / "dictamen.json", informe)
    resumen.update(
        dictamen=informe["dictamen"],
        build=build,
        intentos=informe["intentos"],
        casos_ui_aprobados=informe["casos_ui_aprobados"],
        diseno_sha256=informe["diseno_sha256"],
    )
    print(
        f"{informe['dictamen']} · {informe['intentos']} intentos · {len(informe['casos_ui_aprobados'])} casos UI aprobados"
    )
    return codigo


if __name__ == "__main__":
    principal(__file__, opciones, operar)
