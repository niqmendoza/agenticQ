"""Recuperar evidencia documental acotada para los recorridos solicitados."""

import shutil
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
    run_id,
    write_json,
)


def opciones(parser):
    parser.add_argument("--encargo", type=Path)
    parser.add_argument("--corpus", type=Path)
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
    encargo = read_json(args.encargo)
    run_id(encargo["app"])
    for campo in ("entorno", "build"):
        if not isinstance(encargo[campo], str) or not encargo[campo].strip():
            raise ValueError(f"Falta {campo}.")
    recorridos = encargo["recorridos"]
    ids = [run_id(r["id"]) for r in recorridos]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Se requieren recorridos con IDs únicos.")
    for r in recorridos:
        if (
            r["superficie"] not in ("frontend", "api", "db")
            or not r["objetivo"].strip()
        ):
            raise ValueError(f"Revisá superficie y objetivo de {r['id']}.")
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
    fuentes = salida / "fuentes"
    fuentes.mkdir()
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


def operar(args, salida, logs, resumen):
    """Consultar fuentes y cerrar el análisis de cada recorrido con una regla o una duda."""
    if args.base:
        if args.encargo or args.corpus or args.conservar_indice or not args.revision:
            raise ValueError(
                "Con --base indicá solo la revisión del análisis anterior."
            )
        abrir(args.base, "01-analisis")
        for nombre in ("encargo.json", "analisis.json"):
            shutil.copyfile(args.base / nombre, salida / nombre)
        shutil.copytree(args.base / "fuentes", salida / "fuentes")
        resumen["base_sha256"] = huella(args.base / "entrega.json")
    else:
        if not args.encargo or not args.corpus or not args.corpus.is_dir():
            raise ValueError("Indicá --encargo y un --corpus existente.")
        if salida.resolve().is_relative_to(args.corpus.resolve()):
            raise ValueError(
                "El segundo cerebro debe estar separado de las salidas de V8."
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
        regla["citas"] = [
            citar(f, analisis["extractos"], salida / "fuentes")
            for f in regla["fuentes"]
        ]
    write_json(salida / "reglas.json", reglas)
    resumen.update(
        fase="análisis cerrado",
        revision_sha256=huella(args.revision),
        reglas_pendientes=[k for k, r in reglas.items() if r["estado"] == "pendiente"],
    )
    return 3 if resumen["reglas_pendientes"] else 0


if __name__ == "__main__":
    principal(__file__, opciones, operar)
