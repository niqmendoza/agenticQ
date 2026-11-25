"""Ejecutar exclusivamente el catálogo entregado por diseño y conservar el dictamen."""

import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from credenciales import ARCHIVO_CREDENCIALES, entorno_para, ocultar, referencias
from rutas import EJECUCIONES
from soporte import abrir, huella, principal, read_json, write_json

# isort: split

from alcance import normalizar
from preflight import comprobar
from runners import profile_for_run


def opciones(parser):
    parser.add_argument("--casos", required=True, type=Path)
    parser.add_argument("--chrome-visible", action="store_true")
    parser.add_argument("--credenciales", type=Path, default=ARCHIVO_CREDENCIALES)
    parser.add_argument("--solo-preflight", action="store_true")
    parser.add_argument("--build-ref", help="Commit, digest de imagen o referencia verificable de la release")
    parser.add_argument(
        "--build", help="Repetir la misma suite sobre otro build del mismo entorno"
    )


def operar(args, salida, logs, resumen):
    """Comprobar dependencias y ejecutar el manifiesto con el runner de QA."""
    carpeta = args.casos.resolve()
    abrir(carpeta, "02-casos", requiere="suite.json")
    encargo = normalizar(read_json(carpeta / "encargo.json"))
    casos = read_json(carpeta / "casos.json")
    manifiesto = read_json(carpeta / "pasos.json")
    pendientes = read_json(carpeta / "pendientes.json")
    web = [c for c in casos if c.get("browser_flow") == "web_ui"]
    build = args.build or encargo["build"]
    perfil = profile_for_run(
        read_json(carpeta / "perfil.json"), chrome_visible=args.chrome_visible
    )
    canales = {paso["case"]: paso for paso in manifiesto}
    nombres = {
        nombre for caso in casos for nombre in referencias(caso, canales[caso["id"]], perfil)
    }
    entorno = entorno_para(nombres, args.credenciales)
    secretos = tuple(entorno.get(nombre) for nombre in nombres)
    build_ref = args.build_ref or (encargo.get("build_ref") if build == encargo["build"] else None)
    preflight = comprobar(casos, manifiesto, perfil, entorno)
    preflight.update(interprete=sys.executable, build=build, build_ref=build_ref)
    bloqueos = preflight["bloqueos_por_caso"]
    write_json(logs / "preflight.json", preflight)
    informe = {
        "app": encargo["app"],
        "entorno": encargo["entorno"],
        "build": build,
        "build_ref": build_ref,
        "superficies": encargo["superficies"],
        "solo_preflight": args.solo_preflight,
        "diseno_sha256": huella(carpeta / "entrega.json"),
        "recorridos_solicitados": encargo["recorridos"],
        "casos_ejecutables": len(casos),
        "casos_ui_planificados": [c["id"] for c in web],
        "casos_ui_con_interaccion_observada": [],
        "casos_ui_aprobados": [],
        "pendientes_de_diseno": pendientes,
        "preflight": preflight,
    }
    if args.solo_preflight or len(bloqueos) == len(casos):
        informe.update(
            dictamen="inconclusa",
            intentos=0,
            motivo="Solo diagnóstico." if args.solo_preflight else "Sin casos listos para ejecutar.",
            casos_sin_ejecutar=[c["id"] for c in casos],
        )
        codigo = 0 if args.solo_preflight and casos and not bloqueos else 3
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
        if build_ref:
            cmd.extend(["--build-ref", build_ref])
        if bloqueos:
            bloqueos_archivo = logs / "bloqueos-preflight.json"
            write_json(bloqueos_archivo, bloqueos)
            cmd.extend(["--bloqueos-preflight", str(bloqueos_archivo)])
        runner_log = logs / "runner.log"
        with runner_log.open("w", encoding="utf-8") as log:
            proceso = subprocess.run(
                cmd,
                check=False,
                stdout=log,
                stderr=subprocess.STDOUT,
                env={**entorno, "QC_WORKSPACE": str(trabajo)},
            )
        runner_log.write_text(ocultar(runner_log.read_text(encoding="utf-8", errors="replace"), secretos), encoding="utf-8")
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
            "superficie": recorrido["superficie"],
            "bloqueos_preflight": {c: bloqueos[c] for c in seleccion if c in bloqueos},
            "casos": seleccion,
            "evidencias": [
                por_caso[c]["evidence"]
                for c in seleccion
                if c in por_caso and por_caso[c]["evidence"]
            ],
        }
    informe["cobertura_por_recorrido"] = cobertura
    informe["cobertura_por_superficie"] = {
        superficie: dict(Counter(
            dato["estado"] for dato in cobertura.values() if dato["superficie"] == superficie
        ))
        for superficie in encargo["superficies"]
    }
    informe["alcance"] = {
        "solicitados": len(cobertura),
        "con_casos_publicados": sum(bool(d["casos"]) for d in cobertura.values()),
        "aprobados": sum(d["estado"] == "aprobado" for d in cobertura.values()),
        "pendientes_de_diseno": len(pendientes),
        "casos_bloqueados_preflight": len(bloqueos),
    }
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
