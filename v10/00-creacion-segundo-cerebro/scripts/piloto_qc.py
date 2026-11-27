"""Comprobar cobertura, recuperación y costo estático del piloto QC V3."""

import hashlib
import json
import sys
from collections import Counter, defaultdict
from contextlib import closing
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from soporte import abrir, principal, read_json, run_id, write_json

import brain
from evaluar_okf import auditar_temas, estructura
from fichas import texto
from indice import abrir_indice
from perfil_qc import id_qc
from qc import etiqueta_fuente, ruta_qc
from recuperar_qc import cargar, fragmentos_evidencia
from tematico import planificar

ETAPA = Path(__file__).resolve().parents[1]


def opciones(parser):
    parser.add_argument("--cerebro", required=True, type=Path)
    parser.add_argument("--mapa", required=True, type=Path)
    parser.add_argument("--consultas", required=True, type=Path)
    parser.add_argument("--medir-tokens", action="store_true", help="Usar o200k_base para comparar costos estáticos.")
    parser.add_argument("--consumo-id", type=run_id, help="ID de la etapa donde se importó el corte nativo.")
    parser.add_argument("--republicacion", type=Path, help="Segunda entrega con los mismos insumos para comparar huellas.")
    parser.add_argument("--revision-utilidad", type=Path, help="Evaluación de QC de una muestra de escenarios.")
    parser.add_argument("--justificacion-costo", help="Explicación de un aumento frente a la línea base.")


def preparar_consultas(path):
    raw = read_json(path)
    if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
        raise ValueError("Las consultas QC deben ser una lista de hasta veinte entradas.")
    rows = []
    for row in raw:
        if (
            not isinstance(row, dict) or set(row) - {"tema_base"} != {"id", "consulta", "flujo", "caso"}
            or ("tema_base" in row and type(row["tema_base"]) is not bool)
        ):
            raise ValueError("Cada consulta requiere id, consulta, flujo, caso y tema_base opcional (booleano).")
        rows.append({
            **row, "consulta": texto(row["consulta"], 220, "consulta"),
            **{key: id_qc(row[key], key) for key in ("id", "flujo", "caso")},
        })
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Los IDs de consulta deben ser únicos.")
    if len({r["consulta"].casefold() for r in rows}) != len(rows):
        raise ValueError("Usá consultas distintas para el piloto.")
    return rows


def contiene_caso(pack, probe, case):
    path = ruta_qc(probe["flujo"])
    vistas = {line.split("|", 1)[1] for p in pack["passages"]
              if pack["sources"][p["source"]]["path"] == path for line in p["text"].splitlines()}
    if f"## Caso {probe['caso']}" not in vistas:
        return False
    esperado = {f"[^{etiqueta_fuente(case, ref)}]" for ref in case["evidencia"]}
    return any(line.startswith("**Resultado observable**") and all(mark in line for mark in esperado) for line in vistas)


def evaluar(pack, probe, case, source, budget, usados):
    if case is None:
        return "cobertura", []
    if not contiene_caso(pack, probe, case):
        limits = {"budget", "max-docs", "max-lines"}
        truncated = any(p.get("path") == ruta_qc(probe["flujo"]) and p.get("reason") in limits for p in pack["pending"])
        return ("recorte" if truncated else "seleccion"), []
    if not source:
        return "evidencia", []
    nuevos = {(ref["archivo"], ref["desde"], ref["hasta"]): ref for ref in source}
    if tamano_lote(pack, usados | nuevos) > budget:
        return "recorte", []
    usados.update(nuevos)
    return "recuperado", [f"{ref['archivo']}#L{ref['desde']}-L{ref['hasta']}" for ref in source]


def tamano_lote(pack, fuentes):
    return len(brain.dump({"fichas": pack, "evidencia": list(fuentes.values())}))


def lectura(corpus, fichas, taxonomia, consultas, flujos, perfil, db):
    budget = perfil["presupuesto"]["recuperacion_caracteres"]
    plan = planificar(taxonomia, fichas)
    structural, docs = estructura(corpus, fichas, plan[1], taxonomia)
    with TemporaryDirectory() as tmp:
        index = Path(tmp) / "indice.sqlite"
        brain.index(corpus, index)
        con, cfg, settings = brain.checked(index)
        with closing(con):
            links = defaultdict(set)
            revisadas = Counter()
            for origin, dest in con.execute("SELECT source,target FROM edges"):
                links[origin].add(dest)
                if origin == "index.md":
                    revisadas[dest] += 1
            auditar_temas(corpus, plan, docs, revisadas, structural)
            structural["enlaces_sin_resolver"] = con.execute("SELECT count(*) FROM unresolved").fetchone()[0]
            paths = links["inicio.md"] | {d for p in links["inicio.md"] for d in links[p]}
            critical = perfil["flujos_criticos"].keys()
            structural["flujos_fuera_de_dos_saltos"] = sorted(key for key in critical if ruta_qc(key) not in paths)

            def pack(queries):
                session = brain.session_load(None, cfg["revision"])
                return brain.pack(con, cfg, settings, session, queries, brain.Budget(budget), matched_sections=True)

            batch = pack(list(dict.fromkeys(p["consulta"] for p in consultas)))
            cases, vistos, cache = [], {}, {}
            for probe in consultas:
                flow = flujos.get(probe["flujo"], {})
                case = next((c for c in flow.get("escenarios", []) if c["id"] == probe["caso"]), None)
                evidence = list(fragmentos_evidencia(case, db, cache)) if case else []
                state_one, refs = evaluar(pack([probe["consulta"]]), probe, case, evidence, budget, {})
                state_batch, _ = evaluar(batch, probe, case, evidence, budget, vistos)
                if state_batch == "seleccion" and state_one == "recuperado" and batch["pending_total"] > len(batch["pending"]):
                    # La lista acotada no prueba el motivo. Conservar el diagnóstico observado.
                    state_batch = "seleccion-o-recorte"
                cases.append({**probe, "individual": state_one, "lote": state_batch, "evidencia": refs})
    return structural, {"casos": cases, "individual": dict(Counter(c["individual"] for c in cases)),
                         "lote": dict(Counter(c["lote"] for c in cases)),
                         "presupuesto_caracteres": budget, "caracteres_lote": tamano_lote(batch, vistos)}


def costo(corpus, consultas, perfil, habilitado):
    if not habilitado:
        return {"estado": "sin_medicion"}
    encoder = brain.Budget(2000, 500).encoder
    sizes = {p.relative_to(corpus).as_posix(): len(encoder.encode(p.read_text(encoding="utf-8"), disallowed_special=()))
             for p in corpus.rglob("*.md")}
    rutas = {q["id"]: sizes.get("inicio.md", 0) + sizes[ruta_qc(q["flujo"])] for q in consultas if ruta_qc(q["flujo"]) in sizes}
    base = perfil.get("linea_base_tokens")
    seleccion = [ruta_qc(q["flujo"]) for q in consultas if q.get("tema_base")]
    total_base = sizes["inicio.md"] + sum(sizes[p] for p in set(seleccion)) if seleccion and all(p in sizes for p in seleccion) else None
    return {"estado": "medido", "tokenizer": "o200k_base", "version_tiktoken": version("tiktoken"),
            "inicio_tokens": sizes["inicio.md"],
            "limite_inicio_tokens": perfil["presupuesto"]["portada_tokens"],
            "indice_tokens": sizes["index.md"], "corpus_tokens": sum(sizes.values()), "rutas_tokens": rutas,
            "linea_base_tokens": base, "muestra_base_tokens": total_base,
            "diferencia_linea_base_tokens": total_base - base if base and total_base is not None else None}


def huella_corpus(path):
    receipt = abrir(path, "00-creacion-segundo-cerebro", requiere="fichas-qc.json")
    corpus = {key: value for key, value in receipt["archivos"].items() if key.startswith("corpus/")}
    return hashlib.sha256(json.dumps(corpus, sort_keys=True).encode()).hexdigest()


def revisar_utilidad(path, flujos, commit):
    if not path:
        return None
    raw = read_json(path)
    if (
        not isinstance(raw, dict) or set(raw) != {"por", "commit", "casos"} or raw["commit"] != commit
        or not isinstance(raw["casos"], dict) or not raw["casos"]
    ):
        raise ValueError("La revisión de utilidad requiere responsable, commit actual y casos evaluados.")
    casos = {f"{key}/{c['id']}" for key, flow in flujos.items() for c in flow["escenarios"]}
    output = {}
    for key, value in raw["casos"].items():
        if key not in casos or not isinstance(value, dict) or set(value) != {"util", "detalle"} or type(value["util"]) is not bool:
            raise ValueError("Cada utilidad requiere un escenario publicado, un booleano util y detalle.")
        output[key] = {"util": value["util"], "detalle": texto(value["detalle"], 280, "detalle")}
    return {"por": texto(raw["por"], 120, "responsable"), "commit": commit, "casos": output}


def operar(args, salida, logs, resumen):
    """Emitir un dictamen del piloto documental, separado de la ejecución de pruebas."""
    manifest, flujos = cargar(args.cerebro)
    profile = read_json(args.cerebro / "perfil-qc.json")
    fichas = read_json(args.cerebro / "fichas.json")
    taxonomia = read_json(args.cerebro / "taxonomia.json")
    queries = preparar_consultas(args.consultas)
    corpus = args.cerebro / "corpus"
    abrir(args.mapa, "00-creacion-segundo-cerebro", requiere="indice.sqlite")
    with abrir_indice(args.mapa) as (mapa, db):
        if mapa["commit"] != manifest["commit"] or mapa.get("perfil_qc") != profile:
            raise ValueError("El mapa del piloto debe coincidir con el perfil y el commit de la entrega.")
        structural, retrieval = lectura(corpus, fichas, taxonomia, queries, flujos, profile, db)
    static = costo(corpus, queries, profile, args.medir_tokens)
    utility = revisar_utilidad(args.revision_utilidad, flujos, manifest["commit"])
    if args.justificacion_costo:
        static["justificacion"] = texto(args.justificacion_costo, 280, "justificacion de costo")
    current = huella_corpus(args.cerebro)
    replay = huella_corpus(args.republicacion) if args.republicacion else None
    from diagnosticar import consumo_registrado
    native = consumo_registrado([ETAPA / "logs" / args.consumo_id] if args.consumo_id else [])
    coverage = manifest["qc"]["flujos_criticos"]
    n = len(queries)
    controles = {
        "integridad": not any(structural.get(key) for key in ("incidencias", "enlaces_sin_resolver", "flujos_fuera_de_dos_saltos")),
        "republicacion_identica": current == replay if replay else None,
        "flujos_listos": all(item["estado"] == "listo-para-qc" for item in coverage.values()),
        "recuperacion": n >= 10 and coverage.keys() <= {q["flujo"] for q in queries}
        and all(retrieval[k].get("recuperado", 0) * 10 >= n * 9 for k in ("lote", "individual")),
        "portada": static["inicio_tokens"] <= static["limite_inicio_tokens"] if static["estado"] == "medido" else None,
        "corte_nativo": native["estado"] == "medido" if args.consumo_id else None,
        "costo_frente_a_base": (
            static["diferencia_linea_base_tokens"] <= 0 or bool(static.get("justificacion"))
            if static.get("diferencia_linea_base_tokens") is not None else None
        ) if profile.get("linea_base_tokens") else True,
        "utilidad_revisada": all(row["util"] for row in utility["casos"].values()) if utility else None,
    }
    report = {"commit": manifest["commit"], "app": manifest["app"], "controles": controles,
              "cobertura": coverage, "estructura": structural, "recuperacion": retrieval,
              "costo_estatico": static, "consumo_nativo": native,
              "revision_utilidad": utility,
              "corpus_sha256": current, "republicacion_sha256": replay}
    write_json(salida / "piloto-qc.json", report)
    estado = {True: "cumplido", False: "con hallazgos", None: "pendiente"}
    lines = [
        "# Piloto documental QC V3", "", f"- Aplicación · {manifest['app']}",
        f"- Commit · {manifest['commit']}",
        f"- Recuperación individual · {retrieval['individual'].get('recuperado', 0)}/{n}",
        f"- Recuperación en lote · {retrieval['lote'].get('recuperado', 0)}/{n}",
        f"- Presupuesto · {retrieval['presupuesto_caracteres']} caracteres",
    ]
    if static["estado"] == "medido":
        lines.append(f"- Tokens estáticos de la portada y el corpus · {static['inicio_tokens']} y {static['corpus_tokens']}")
    lines += ["", "## Controles", "", *[f"- {key.replace('_', ' ')} · {estado[value]}" for key, value in controles.items()]]
    (salida / "piloto-qc.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    resumen.update(operacion="piloto-qc", commit=manifest["commit"], controles=controles)
    return 0 if all(value is True for value in controles.values()) else 3


if __name__ == "__main__":
    principal(__file__, opciones, operar)
