"""Persistencia y trazabilidad compartidas por las etapas de V10."""

import argparse
import hashlib
import os
import subprocess
import sys
from contextlib import nullcontext
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from uuid import uuid4

from consolidar import consolidar
from higiene import sanear
from rutas import ANALISIS, cargar_motor

cargar_motor()

from session import read_json, run_id, timestamp, write_json
from token_meter import select_usage


def paquete_documental(corpus, consultas, max_chars, logs, conservar_indice=False):
    navegacion = logs / "navegacion"
    if conservar_indice:
        navegacion.mkdir()
    espacio = nullcontext(navegacion) if conservar_indice else TemporaryDirectory()
    with espacio as temporal:
        tmp = Path(temporal)
        write_json(tmp / "consultas.json", consultas)
        base = [
            sys.executable,
            str(ANALISIS / "brain.py"),
            "--db",
            str(tmp / "indice.sqlite"),
            "--session",
            str(tmp / "sesion.json"),
        ]
        if conservar_indice:
            base.extend(["--log-dir", str(navegacion)])
        for nombre, parametros in [
            ("index", [str(corpus.resolve())]),
            (
                "pack",
                [
                    "--matched-sections",
                    "--queries-json",
                    str(tmp / "consultas.json"),
                    "--max-chars",
                    str(max_chars),
                ],
            ),
        ]:
            archivo = tmp / f"{nombre}.json"
            with archivo.open("w") as salida_motor:
                proceso = subprocess.run(
                    [*base, nombre, *parametros],
                    check=False,
                    stdout=salida_motor,
                    stderr=subprocess.PIPE,
                    encoding="utf-8",
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )
            if proceso.returncode and not archivo.stat().st_size:
                raise ValueError(
                    f"El motor no pudo ejecutar {nombre}. Verificá el intérprete y la revisión de los scripts incluida en el paquete."
                )
            datos = read_json(archivo)
            if proceso.returncode:
                raise ValueError(datos.get("error", f"Falló {nombre}"))
            if nombre == "index":
                write_json(logs / "indice.json", datos)
    return datos


def huella(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for bloque in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def inventario(root):
    return {
        p.relative_to(root).as_posix(): huella(p)
        for p in sorted(root.rglob("*"))
        if p.is_file() and p != root / "entrega.json"
    }


class CitaInvalida(ValueError):
    def __init__(self, causa, fuente, disponibles=()):
        campos = fuente if isinstance(fuente, dict) else {}
        nombre = campos.get("path")
        limites = [campos.get("start"), campos.get("end")]
        self.datos = {
            "causa": causa,
            "archivo": sanear(nombre)[0] if isinstance(nombre, str) else None,
            "rango": limites if all(type(limite) is int for limite in limites) else None,
            "rangos_disponibles": list(disponibles),
        }
        super().__init__(f"{causa}: {self.datos['archivo']}")


def citar(fuente, extractos, carpeta):
    """Reconstruir una cita contra texto entregado e informar la causa precisa."""
    from contracts import valid_sources

    if (
        not valid_sources([fuente]) or ("start" in fuente) != ("end" in fuente)
        or "start" in fuente and (
            type(fuente["start"]) is not int or type(fuente["end"]) is not int
            or not 1 <= fuente["start"] <= fuente["end"]
        )
        or "locator" in fuente and (
            not isinstance(fuente["locator"], str) or not fuente["locator"].strip()
        )
    ):
        raise CitaInvalida("formato_cita", fuente)
    candidatos = [e for e in extractos if fuente["path"] == e["original"]]
    if not candidatos:
        raise CitaInvalida("archivo_ausente", fuente)
    rangos = sorted({(e["desde"], e["hasta"]) for e in candidatos})
    coincidencias = {}
    rango_entregado = False
    for e in candidatos:
        inicio, fin = fuente.get("start", e["desde"]), fuente.get("end", e["hasta"])
        if not e["desde"] <= inicio <= fin <= e["hasta"]:
            continue
        rango_entregado = True
        fragmento = carpeta / e["archivo"]
        texto = fragmento.read_text(encoding="utf-8").splitlines()
        localizador = fuente.get("locator", "").casefold()
        a, b = inicio - e["desde"], fin - e["desde"] + 1
        contenido = "\n".join(texto[a:b]).casefold()
        if not localizador:
            posiciones = [0]
        else:
            posiciones = []
            pos = contenido.find(localizador)
            while pos >= 0:
                posiciones.append(pos)
                pos = contenido.find(localizador, pos + len(localizador))
        for pos in posiciones:
            desde, hasta = a, b
            if "start" not in fuente:
                desde += contenido.count("\n", 0, pos)
                hasta = desde + localizador.count("\n") + 1
            absoluto = (e["desde"] + desde, e["desde"] + hasta - 1)
            coincidencias.setdefault(absoluto, {
                **fuente,
                "path": e["archivo"],
                "start": desde + 1,
                "end": hasta,
                "sha256": huella(fragmento),
            })
    if len(coincidencias) == 1:
        return next(iter(coincidencias.values()))
    causa = ("localizador_ambiguo" if coincidencias else
             "texto_no_coincide" if rango_entregado else "rango_ausente")
    raise CitaInvalida(causa, fuente, rangos)


def exigir_citas(errores, logs):
    if errores:
        write_json(logs / "citas-invalidas.json", errores)
        causas = ", ".join(sorted({error["causa"] for error in errores}))
        raise ValueError(f"{len(errores)} citas requieren corrección ({causas}). Revisá citas-invalidas.json.")

def abrir(root, etapa, *, requiere=None):
    recibo = read_json(root / "entrega.json")
    if recibo["etapa"] != etapa or recibo["archivos"] != inventario(root):
        raise ValueError(f"La entrega de {etapa} está incompleta o cambió.")
    if requiere and requiere not in recibo["archivos"]:
        raise ValueError(
            f"Se esperaba una entrega de {etapa} que incluya {requiere}. Revisá la carpeta de entrada."
        )
    return recibo


def consumo(args, etapa):
    carpeta = etapa / "logs" / run_id(args.id)
    if not any(carpeta.glob("*/resumen.json")):
        raise ValueError("No existe una ejecución registrada con ese ID en esta etapa.")
    scope, llamadas = select_usage(args.archivo, args.formato, args.scope, include_cache=True)
    valores = list(llamadas.values())

    def total(filas, indice):
        return (
            sum(v[indice] for v in filas)
            if all(v[indice] is not None for v in filas)
            else None
        )

    por_modelo = defaultdict(list)
    for fila in valores:
        por_modelo[sanear(fila[4])[0] if fila[4] else "sin identificar"].append(fila)
    registro = {
        "corte_utc": timestamp(),
        "formato": args.formato,
        "conversacion_sha256": hashlib.sha256(scope.encode()).hexdigest(),
        "llamadas_unicas": len(valores),
        "tokens_entrada": total(valores, 2),
        "tokens_salida": total(valores, 3),
        "tokens_cache_lectura": total(valores, 5),
        "llamadas_sin_entrada": sum(v[2] is None for v in valores),
        "llamadas_sin_salida": sum(v[3] is None for v in valores),
        "inicio_llamadas": min(v[0] for v in valores).isoformat(),
        "fin_llamadas": max(v[1] for v in valores).isoformat(),
        "por_modelo": {
            nombre: {"llamadas": len(filas), "tokens_entrada": total(filas, 2), "tokens_salida": total(filas, 3)}
            for nombre, filas in sorted(por_modelo.items())
        },
        "fuente_sha256": huella(args.archivo),
    }
    destino = carpeta / f"consumo-{uuid4().hex}.json"
    write_json(destino, registro)
    print(destino)


def principal(script, configurar, operar):
    etapa = Path(script).resolve().parents[1]
    parser = argparse.ArgumentParser(description=operar.__doc__)
    comandos = parser.add_subparsers(dest="accion", required=True)
    ejecutar = comandos.add_parser("procesar")
    ejecutar.add_argument("--id", required=True, type=run_id)
    configurar(ejecutar)
    medir = comandos.add_parser(
        "medir", help="Adjuntar corte nativo de una conversación exclusiva de la etapa"
    )
    medir.add_argument("--id", required=True, type=run_id)
    medir.add_argument("--archivo", required=True, type=Path)
    medir.add_argument("--scope", help="ID de conversación. El script lo infiere si la fuente contiene una sola.")
    medir.add_argument("--formato", choices=("otel", "native"), default="otel")
    reunir = comandos.add_parser("consolidar", help="Generar el Markdown de todos los IDs indicados")
    reunir.add_argument("--id", action="append", required=True, type=run_id)
    args = parser.parse_args()
    if args.accion == "consolidar":
        for identificador in args.id:
            if not (etapa / "logs" / identificador).is_dir():
                parser.exit(2, f"No existe el ID {identificador} en esta etapa.\n")
        print(consolidar(etapa, args.id))
        return
    if args.accion == "medir":
        try:
            consumo(args, etapa)
            consolidar(etapa, [args.id], individual=True)
        except (ValueError, OSError) as exc:
            parser.exit(2, f"{exc}\n")
        return
    inicio = monotonic()
    logs = etapa / "logs" / args.id / uuid4().hex
    logs.mkdir(parents=True)
    resumen = {
        "etapa": etapa.name,
        "id": args.id,
        "inicio_utc": timestamp(),
        "estado": "en curso",
        "consumo_agente": "Cortes nativos por conversación en ../consumo-*.json. Sin corte, el consumo es desconocido.",
        "llamadas_modelo_del_script": 0,
    }
    write_json(logs / "resumen.json", resumen)
    destino = etapa / "salidas" / args.id
    destino.parent.mkdir(exist_ok=True)
    bloqueo = destino.parent / f".{args.id}.en-curso"
    propietario = False
    codigo = 2
    try:
        bloqueo.mkdir()
        propietario = True
        if destino.exists():
            raise ValueError("Ese ID ya tiene una entrega. Elegí un ID nuevo.")
        with TemporaryDirectory(dir=destino.parent) as temporal:
            borrador = Path(temporal) / "entrega"
            borrador.mkdir()
            codigo = operar(args, borrador, logs, resumen)
            write_json(
                borrador / "entrega.json",
                {"etapa": etapa.name, "id": args.id, "archivos": inventario(borrador)},
            )
            os.rename(borrador, destino)
        resumen["entrega"] = str(destino)
        resumen["entrega_sha256"] = huella(destino / "entrega.json")
        print(destino)
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        IndexError,
        AttributeError,
    ) as exc:
        codigo = 2
        mensaje = sanear(str(exc))[0]
        resumen["error"] = mensaje
        print(mensaje, file=sys.stderr)
    finally:
        resumen.update(
            fin_utc=timestamp(),
            duracion_segundos=round(monotonic() - inicio, 3),
            codigo=codigo,
            estado={0: "completada", 1: "rechazada", 2: "error", 3: "inconclusa"}.get(
                codigo, "error"
            ),
        )
        write_json(logs / "resumen.json", resumen)
        if propietario:
            bloqueo.rmdir()
        try:
            print(f"Consolidado: {consolidar(etapa, [args.id], individual=True)}", file=sys.stderr)
        except OSError as error:
            print(f"No se pudo consolidar el log: {error}", file=sys.stderr)
            codigo = 2
        print(f"Log: {logs}", file=sys.stderr)
    raise SystemExit(codigo)
