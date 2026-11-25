"""Recuperar evidencia documental acotada para los recorridos solicitados."""

import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from soporte import (
    abrir,
    citar,
    huella,
    paquete_documental,
    principal,
    read_json,
    write_json,
)

from alcance import normalizar
from brain import Budget, checked, session_load, show


def opciones(parser):
    parser.add_argument("--encargo", type=Path)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--validar-encargo", action="store_true")
    parser.add_argument("--indice", type=Path, help="indice.sqlite de una recuperación conservada")
    parser.add_argument(
        "--agregar-rango", nargs=3, action="append",
        metavar=("ARCHIVO", "DESDE", "HASTA"),
        help="Incorporar un rango citable a partir del índice y la entrega indicados",
    )
    parser.add_argument(
        "--base",
        type=Path,
        help="Recuperación anterior, para cerrar el análisis sin reindexar",
    )
    parser.add_argument(
        "--revision",
        type=Path,
        help="Reglas y dudas por recorrido derivadas de los extractos",
    )
    parser.add_argument("--max-chars", type=int, default=16000)
    parser.add_argument(
        "--conservar-indice",
        action="store_true",
        help="Guardar índice y sesión en logs para consultas puntuales posteriores",
    )


def recuperar(args, salida, logs, resumen):
    """Indexar el segundo cerebro y preparar extractos citables."""
    encargo = normalizar(read_json(args.encargo))
    recorridos = encargo["recorridos"]
    ids = [r["id"] for r in recorridos]
    if args.max_chars < 3000:
        raise ValueError("Usá al menos 3000 caracteres para el contexto.")
    consultas = list(
        dict.fromkeys(r.get("consulta", r["objetivo"]) for r in recorridos)
    )
    if len(consultas) > 20:
        raise ValueError("Agrupá las consultas del encargo en hasta 20 búsquedas.")
    write_json(salida / "encargo.json", encargo)
    datos = paquete_documental(
        args.corpus, consultas, args.max_chars, logs,
        conservar_indice=args.conservar_indice,
    )
    if args.conservar_indice:
        resumen["navegacion"] = str(logs / "navegacion")
    extractos = guardar_extractos(datos, salida)
    analisis = {
        "revision": datos["revision"],
        "consultas": datos["queries"],
        "extractos": extractos,
        "pendientes": datos["pending"],
        "total_pendientes_motor": datos["pending_total"],
    }
    write_json(salida / "analisis.json", analisis)
    resumen.update(
        encargo_sha256=huella(args.encargo),
        recorridos=ids,
        revision=datos["revision"],
        extractos=len(extractos),
        caracteres_extractos=sum(len(p["text"]) for p in datos["passages"]),
        presupuesto_caracteres=args.max_chars,
    )
    return 0 if extractos else 3


def guardar_extractos(datos, salida):
    fuentes = salida / "fuentes"
    fuentes.mkdir(exist_ok=True)
    extractos = []
    for p in datos["passages"]:
        fuente = datos["sources"][p["source"]]
        nombre = f"{p['source']}-{p['start']}-{p['end']}.txt"
        texto = "\n".join(linea.partition("|")[2] for linea in p["text"].split("\n"))
        (fuentes / nombre).write_text(texto + "\n", encoding="utf-8")
        extractos.append(
            {
                "archivo": nombre,
                "original": fuente["path"],
                "sha256_original": fuente["sha256"],
                "desde": p["start"],
                "hasta": p["end"],
            }
        )
    return extractos


def ampliar(args, salida, logs, resumen):
    if not args.indice.is_file():
        raise ValueError("No se encontró el índice conservado.")
    try:
        conexion, config, _ = checked(args.indice)
    except sqlite3.Error:
        raise ValueError("El índice conservado no es válido.") from None
    try:
        analisis = read_json(salida / "analisis.json")
        if analisis["revision"] != config["revision"]:
            raise ValueError("El índice pertenece a otra revisión del corpus.")
        entrega = {e["archivo"]: e for e in analisis["extractos"]}
        for ruta, primero, ultimo in args.agregar_rango:
            inicio, fin = int(primero), int(ultimo)
            if inicio < 1 or fin < inicio or fin - inicio >= 200:
                raise ValueError("Cada rango debe tener entre 1 y 200 líneas.")
            sesion = session_load(None, config["revision"])
            datos = show(conexion, config, sesion, ruta, inicio, fin, 200, Budget(args.max_chars))
            if datos.get("beyond_eof") or not datos.get("range_complete"):
                raise ValueError("El rango excede el documento o el presupuesto. Acotalo y reintentá.")
            for extracto in guardar_extractos(datos, salida):
                entrega[extracto["archivo"]] = extracto
        analisis["extractos"] = list(entrega.values())
        write_json(salida / "analisis.json", analisis)
        write_json(logs / "rangos.json", args.agregar_rango)
        resumen["rangos_agregados"] = len(args.agregar_rango)
    finally:
        conexion.close()


def operar(args, salida, logs, resumen):
    """Consultar fuentes y cerrar el análisis de cada recorrido con una regla o una duda."""
    if args.validar_encargo:
        if not args.encargo or any((args.base, args.corpus, args.revision, args.indice, args.agregar_rango)):
            raise ValueError("Con --validar-encargo indicá únicamente --encargo.")
        encargo = normalizar(read_json(args.encargo))
        write_json(salida / "encargo.json", encargo)
        resumen.update(fase="encargo validado", app_id=encargo["app_id"], superficies=encargo["superficies"])
        return 0
    if bool(args.indice) != bool(args.agregar_rango) or (args.indice and not args.base):
        raise ValueError("Para agregar rangos indicá --base, --indice y --agregar-rango.")
    if args.base:
        if args.encargo or args.corpus or args.conservar_indice or not (args.revision or args.agregar_rango):
            raise ValueError("Con --base indicá --revision, rangos adicionales o ambos.")
        abrir(args.base, "01-analisis")
        for nombre in ("encargo.json", "analisis.json"):
            shutil.copyfile(args.base / nombre, salida / nombre)
        shutil.copytree(args.base / "fuentes", salida / "fuentes")
        resumen["base_sha256"] = huella(args.base / "entrega.json")
        if args.agregar_rango:
            ampliar(args, salida, logs, resumen)
    else:
        if not args.encargo or not args.corpus or not args.corpus.is_dir():
            raise ValueError("Indicá --encargo y un --corpus existente.")
        if salida.resolve().is_relative_to(args.corpus.resolve()):
            raise ValueError(
                "El segundo cerebro debe estar separado de las salidas de V9."
            )
        recuperar(args, salida, logs, resumen)
    if args.revision is None:
        resumen["fase"] = "contexto recuperado; falta revisar reglas"
        print("Contexto disponible. Cerrá la etapa con --base y --revision.")
        return 0 if read_json(salida / "analisis.json")["extractos"] else 3
    reglas = read_json(args.revision)
    encargo = read_json(salida / "encargo.json")
    if set(reglas) != {r["id"] for r in encargo["recorridos"]}:
        raise ValueError("La revisión debe incluir todos los recorridos del encargo.")
    analisis = read_json(salida / "analisis.json")
    for clave, regla in reglas.items():
        if (
            regla["estado"] not in ("documentada", "pendiente")
            or not regla["detalle"].strip()
        ):
            raise ValueError(
                f"{clave}: indicá la regla funcional o la duda por resolver."
            )
        if regla["estado"] == "documentada" and not regla["fuentes"]:
            raise ValueError(f"{clave}: la regla necesita al menos una cita.")
        try:
            regla["citas"] = [
                citar(f, analisis["extractos"], salida / "fuentes")
                for f in regla["fuentes"]
            ]
        except ValueError as error:
            raise ValueError(f"{clave}: {error}") from error
    write_json(salida / "reglas.json", reglas)
    resumen.update(
        fase="análisis cerrado",
        revision_sha256=huella(args.revision),
        reglas_pendientes=[k for k, r in reglas.items() if r["estado"] == "pendiente"],
    )
    return 3 if resumen["reglas_pendientes"] else 0


if __name__ == "__main__":
    principal(__file__, opciones, operar)
