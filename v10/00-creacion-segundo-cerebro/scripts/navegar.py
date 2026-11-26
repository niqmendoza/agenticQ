"""Entregar a Copilot un mapa, resultados de búsqueda o rangos con presupuesto estricto."""

import heapq
import json
import re
import sys
from itertools import islice
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from higiene import sanear
from soporte import principal, write_json

from indice import abrir_indice, archivo

STOP = {"que", "para", "con", "del", "por", "una", "los", "las", "and", "for", "the", "how", "what"}


def opciones(parser):
    parser.add_argument("--mapa", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--resumen", action="store_true")
    mode.add_argument("--consulta", action="append", help="Búsqueda de términos. Se puede repetir.")
    mode.add_argument("--rango", nargs=3, metavar=("ARCHIVO", "DESDE", "HASTA"))
    parser.add_argument("--modulo")
    parser.add_argument("--max-chars", type=int, default=7000)
    parser.add_argument("--limite", type=int, default=12, help="Máximo de entradas publicadas.")
    parser.add_argument("--desplazamiento", type=int, default=0, help="Cantidad de filas a saltar en --resumen.")


def tamano(value):
    return len(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)) + 1


def enumerar(data, db, module):
    if module:
        for row in db.execute(
            "SELECT ruta, tipo, lineas, simbolos FROM archivos WHERE modulo=? "
            "ORDER BY CASE tipo WHEN 'contrato' THEN 0 WHEN 'documentacion' THEN 1 "
            "WHEN 'pruebas' THEN 2 ELSE 3 END, ruta", (module,),
        ):
            yield {
                "archivo": row["ruta"], "tipo": row["tipo"], "lineas": row["lineas"],
                "simbolos_detectados": json.loads(row["simbolos"])[:5],
            }
    else:
        for key, info in sorted(data["modulos"].items()):
            yield {"modulo": key, "archivos": info["archivos"], "tipos": info["cantidades"],
                   "depende_de": info["depende_de"], "revision": info.get("revision", "pendiente")}


def top_hits(db, queries, module, limit):
    terms = [tuple(dict.fromkeys(t for t in re.findall(r"\w{2,}", query.casefold()) if t not in STOP)) for query in queries]
    if any(not tokens or len(tokens) > 14 for tokens in terms):
        raise ValueError("Usá hasta 14 términos relevantes por consulta.")
    heaps = [[] for _ in queries]
    sql = "SELECT ruta, tipo, texto FROM archivos" + (" WHERE modulo=?" if module else "") + " ORDER BY ruta"
    for row in db.execute(sql, (module,) if module else ()):
        source = row["texto"].split("\n")
        lower = row["texto"].casefold()
        path = row["ruta"]
        for index, tokens in enumerate(terms):
            if not any(term in lower for term in tokens):
                continue
            hits = []
            for lineno, line in enumerate(source):
                folded = line.casefold()
                matched = sum(term in folded for term in tokens)
                if matched:
                    score = 6 * matched + 3 * (queries[index].casefold() in folded)
                    score += sum(term in path.casefold() for term in tokens)
                    hits.append((score, lineno))
            picked = []
            for score, lineno in sorted(hits, key=lambda hit: (-hit[0], hit[1])):
                if any(abs(lineno - previous) < 5 for previous in picked):
                    continue
                picked.append(lineno)
                start, end = max(0, lineno - 2), min(len(source), lineno + 4)
                text = [entry[:300] for entry in source[start:end]]
                entry = (
                    score, path, start + 1, end, row["tipo"], "\n".join(text),
                    any(len(line) > 300 for line in source[start:end]),
                )
                if len(heaps[index]) < limit:
                    heapq.heappush(heaps[index], entry)
                else:
                    heapq.heappushpop(heaps[index], entry)
                if len(picked) == 3:
                    break
    ordered = [sorted(heap, key=lambda h: (-h[0], h[1], h[2])) for heap in heaps]
    delivered = set()
    for rank in range(limit):
        for i, hits in enumerate(ordered):
            if rank >= len(hits):
                continue
            _, path, start, end, kind, text, clipped = hits[rank]
            key = (path, start, end)
            if key in delivered:
                continue
            delivered.add(key)
            yield {"consulta": i + 1, "archivo": path, "desde": start, "hasta": end,
                   "tipo": kind, "texto": text, "lineas_recortadas": clipped}


def operar(args, salida, logs, resumen):
    """Emitir solo los fragmentos o rutas necesarios, con un límite sobre todo el JSON."""
    modo = "resumen" if args.resumen else "buscar" if args.consulta else "rango"
    resumen.update(operacion=modo, presupuesto_caracteres=args.max_chars)
    if not 800 <= args.max_chars <= 30000 or not 1 <= args.limite <= 50:
        raise ValueError("Indicá entre 800 y 30000 caracteres y entre 1 y 50 entradas.")
    if args.desplazamiento < 0 or args.desplazamiento and not args.resumen:
        raise ValueError("El desplazamiento se usa con --resumen y debe ser positivo o cero.")
    with abrir_indice(args.mapa) as (mapa, db):
        if args.modulo and args.modulo not in mapa["modulos"]:
            raise ValueError("El módulo no existe en el mapa.")
        resumen.update(commit=mapa["commit"], modulo=args.modulo)
        contexto = {
            "commit": mapa["commit"], "modo": modo, "modulo": args.modulo,
            "presupuesto_caracteres": args.max_chars, "recortado": False, "entradas": [],
        }
        if args.resumen:
            contexto["app"] = mapa["app"]
            contexto["total_modulos"] = len(mapa["modulos"])
            contexto["archivos_indexados"] = mapa["archivos_indexados"]
            contexto["desplazamiento"] = args.desplazamiento
            candidatos = islice(enumerar(mapa, db, args.modulo), args.desplazamiento, None)
        elif args.consulta:
            queries = list(dict.fromkeys(q.strip() for q in args.consulta))
            if len(queries) > 10 or any(not q or len(q) > 180 or sanear(q)[1] for q in queries):
                raise ValueError("Usá hasta diez consultas breves, sin valores sensibles.")
            contexto["consultas"] = queries
            resumen["consultas"] = len(queries)
            candidatos = top_hits(db, queries, args.modulo, args.limite)
        else:
            path, a, b = args.rango
            row = archivo(db, path)
            a, b = int(a), int(b)
            if not 1 <= a <= b <= row["lineas"] or b - a >= 80 or (args.modulo and row["modulo"] != args.modulo):
                raise ValueError("El rango debe existir en el archivo, incluir hasta 80 líneas y pertenecer al módulo.")
            candidatos = [{
                "archivo": row["ruta"], "desde": a, "hasta": b,
                "tipo": row["tipo"], "texto": "\n".join(row["texto"].split("\n")[a - 1:b]),
            }]
        if tamano(contexto) > args.max_chars:
            raise ValueError("El presupuesto no alcanza para los metadatos. Acotá las consultas.")
        for candidato in candidatos:
            if len(contexto["entradas"]) == args.limite:
                contexto["recortado"] = True
                break
            contexto["entradas"].append(candidato)
            if tamano(contexto) > args.max_chars:
                contexto["entradas"].pop()
                contexto["recortado"] = True
                if args.rango:
                    raise ValueError("El rango supera el presupuesto. Pedí menos líneas o ampliá el límite.")
    write_json(salida / "contexto.json", contexto)
    fragmentos = [entry["texto"] for entry in contexto["entradas"] if "texto" in entry]
    resumen.update(
        operacion=modo, commit=contexto["commit"], entradas=len(contexto["entradas"]),
        caracteres_contexto=tamano(contexto),
        fragmentos=len(fragmentos), caracteres_fragmentos=sum(map(len, fragmentos)),
        presupuesto_caracteres=args.max_chars, contexto_recortado=contexto["recortado"],
        caracteres_fuente=mapa["caracteres_fuente"],
    )
    return 0 if contexto["entradas"] else 3


if __name__ == "__main__":
    principal(__file__, opciones, operar)
