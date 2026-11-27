"""Comprobaciones estructurales y sondas con el mismo motor de recuperación de la etapa 01."""

import re
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import yaml

import brain
from fichas import texto
from okf import VERSION_OKF, linea_enlace, ruta_concepto, texto_seguro
from repositorio import ID
from tematico import linea_relacion, planificar, vinculo

NOTAS = re.compile(r"\[\^([^\]\n]+)\](?!:)")
DEFINICIONES = re.compile(r"^\[\^([^\]\n]+)\]:", re.MULTILINE)


def cabecera(content):
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        return None, "\n".join(lines)
    try:
        end = lines.index("---", 1)
        data = yaml.safe_load("\n".join(lines[1:end]))
    except (ValueError, yaml.YAMLError):
        raise ValueError("frontmatter_invalido") from None
    if not isinstance(data, dict):
        raise ValueError("frontmatter_invalido")
    return data, "\n".join(lines[end + 1:])


def estructura(corpus, fichas, rutas, taxonomia):
    hechos = set(rutas.values()) if taxonomia else {
        ruta_concepto(key, hecho["id"])
        for key, ficha in fichas.items()
        for hecho in ficha["hechos"]
    }
    afirmaciones = defaultdict(list)
    for key, ficha in fichas.items():
        for hecho in ficha["hechos"]:
            afirmaciones[" ".join(hecho["afirmacion"].casefold().split())].append(
                f"{key}/{hecho['id']}"
            )
    types, incidencias = Counter(), []
    chars = 0
    roots = {"index.md", "aplicacion.md"}
    if taxonomia:
        roots.update(f"temas/{area['id']}/index.md" for area in taxonomia["areas"])
        roots.update(f"mocs/{moc['id']}.md" for moc in taxonomia["mocs"])
    else:
        roots.add("modulos/index.md")
        for key in fichas:
            roots.update({f"modulos/{key}/index.md", f"modulos/{key}/modulo.md"})
    for path in sorted(roots | hechos):
        if not (corpus / path).is_file():
            incidencias.append({"archivo": path, "causa": "archivo_ausente"})
    docs = {}
    for doc in sorted(corpus.rglob("*.md")):
        path = doc.relative_to(corpus).as_posix()
        content = doc.read_text(encoding="utf-8")
        chars += len(content)
        try:
            meta, body = cabecera(content)
        except ValueError:
            incidencias.append({"archivo": path, "causa": "frontmatter_invalido"})
            continue
        if path == "index.md":
            if meta != {"okf_version": VERSION_OKF}:
                incidencias.append({"archivo": path, "causa": "version_okf_incorrecta"})
            continue
        if doc.name in {"index.md", "log.md"}:
            if meta is not None:
                incidencias.append({"archivo": path, "causa": "frontmatter_en_archivo_reservado"})
            continue
        if not meta or not isinstance(meta.get("type"), str) or not meta["type"].strip():
            incidencias.append({"archivo": path, "causa": "tipo_ausente"})
            continue
        types[meta["type"]] += 1
        docs[path] = meta
        if path in hechos:
            sources = meta.get("sources")
            claves = [
                ref.get("id") for ref in sources
                if isinstance(ref, dict) and isinstance(ref.get("resource"), str)
                and ref["resource"].strip() and isinstance(ref.get("id"), str) and ref["id"].strip()
            ] if isinstance(sources, list) else []
            invocadas = set(NOTAS.findall(body))
            if (
                not claves or len(set(claves)) != len(sources) or set(claves) != invocadas
                or set(claves) != set(DEFINICIONES.findall(body))
            ):
                incidencias.append({"archivo": path, "causa": "atribucion_incompleta"})
    return {
        "documentos_okf": len(docs), "conceptos_de_qa": len(hechos & docs.keys()),
        "por_tipo": dict(sorted(types.items())), "caracteres_markdown": chars,
        "afirmaciones_repetidas": [ids for ids in afirmaciones.values() if len(ids) > 1],
        "incidencias": incidencias,
    }, docs


def configurar_sondas(spec, fichas, plan=None):
    if spec is None:
        if plan:
            taxonomia, _, notas, *_ = plan
            return "titulos_por_area", [
                {"id": f"sonda-{number}", "consulta": notas[key]["titulo"], "concepto": key}
                for number, area in enumerate(taxonomia["areas"][:6], 1)
                if (key := next((item for item in area["conceptos"] if item in notas), None))
            ]
        grupos = [(key, sorted(ficha["hechos"], key=lambda item: item["id"])) for key, ficha in sorted(fichas.items())]
        probes = []
        for key, hechos in grupos:
            if hechos and len(probes) < 6:
                hecho = hechos[0]
                probes.append({
                    "id": f"sonda-{len(probes) + 1}", "consulta": f"{key} {hecho['titulo']}",
                    "concepto": f"{key}/{hecho['id']}",
                })
        return "titulos_del_bundle", probes
    if not isinstance(spec, list) or not 1 <= len(spec) <= 12:
        raise ValueError("Las pruebas de recuperación deben ser una lista de una a doce consultas.")
    revisadas = []
    for item in spec:
        if not isinstance(item, dict) or set(item) - {"id", "consulta", "concepto", "localizador"}:
            raise ValueError("Cada prueba requiere id, consulta, concepto y un localizador opcional.")
        key, concept = item.get("id"), item.get("concepto")
        if not isinstance(key, str) or not ID.fullmatch(key) or any(row["id"] == key for row in revisadas):
            raise ValueError("El ID de cada prueba debe ser único y usar letras minúsculas, números o guiones.")
        if not isinstance(concept, str) or not re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+", concept):
            raise ValueError("Indicá el concepto esperado como modulo/id.")
        revisadas.append({
            "id": key, "consulta": texto(item.get("consulta"), 220, "consulta"),
            "concepto": concept,
            **({"localizador": texto(item["localizador"], 220, "localizador")} if "localizador" in item else {}),
        })
    return "expectativas_de_qa", revisadas


def evaluar_sonda(probe, paquete, docs, rutas):
    key = probe["concepto"]
    path = rutas.get(key, ruta_concepto(*key.split("/")))
    extractos = [
        p for p in paquete["passages"] if paquete["sources"][p["source"]]["path"] == path
    ]
    locator = probe.get("localizador", "").casefold()
    if path not in docs:
        estado = "concepto_ausente"
    elif not extractos:
        estado = "concepto_no_recuperado"
    elif locator and not any(
        locator in "\n".join(line.partition("|")[2] for line in p["text"].splitlines()).casefold()
        for p in extractos
    ):
        estado = "localizador_no_recuperado"
    else:
        estado = "recuperado"
    return {
        "estado": estado,
        "rangos_recuperados": [[p["start"], p["end"]] for p in extractos],
    }


def auditar_temas(corpus, plan, docs, conteo_raiz, structure):
    taxonomia, rutas, notas, salientes, entrantes, errores = plan

    def comprobar_lineas(path, expected):
        file = corpus / path
        if not file.is_file():
            return False
        actual = set(file.read_text(encoding="utf-8").splitlines())
        return all(line in actual for line in expected)

    aislados = []
    for key, path in rutas.items():
        if conteo_raiz[path] != 1:
            errores.append({"causa": "indice_raiz_incorrecto", "concepto": key, "apariciones": conteo_raiz[path]})
        meta = docs.get(path, {})
        if meta.get("description") != notas[key].get("descripcion") or meta.get("qa_estado") != notas[key].get("estado"):
            errores.append({"causa": "metadatos_del_concepto_incorrectos", "concepto": key})
        relaciones = [linea_relacion(e, rutas, notas, path) for e in salientes[key] if e["destino"] in rutas]
        backlinks = [linea_relacion(e, rutas, notas, path, entrante=True) for e in entrantes[key] if e["origen"] in rutas]
        if not (relaciones or backlinks) or not any(comprobar_lineas(path, [line]) for line in relaciones + backlinks):
            aislados.append(key)
        if not comprobar_lineas(path, relaciones + backlinks):
            errores.append({"causa": "relacion_no_renderizada", "concepto": key})
    for moc in taxonomia["mocs"]:
        path = f"mocs/{moc['id']}.md"
        expected = [
            linea_enlace(notas[e["destino"]]["titulo"], vinculo(path, rutas[e["destino"]]), texto_seguro(e["motivo"]))
            for e in moc["conceptos"] if e["destino"] in rutas
        ]
        if not comprobar_lineas(path, expected):
            errores.append({"causa": "moc_incompleto", "moc": moc["id"]})
    errores.extend({"causa": "concepto_aislado_en_bundle", "concepto": key} for key in aislados)
    structure["incidencias"].extend(errores)
    structure["grafo_tematico"] = {
        "estado": "observado" if not errores else "con_incidencias",
        "areas": len(taxonomia["areas"]), "mocs": len(taxonomia["mocs"]),
        "indice_raiz_unico": sum(conteo_raiz[path] == 1 for path in rutas.values()),
        "relaciones_justificadas": sum(map(len, salientes.values())),
        "relaciones_entre_areas": sum(
            rutas[key].split("/")[1] != rutas[e["destino"]].split("/")[1]
            for key, edges in salientes.items() if key in rutas
            for e in edges if e["destino"] in rutas
        ),
        "conceptos_aislados": aislados,
    }


def evaluar_lectura(corpus, fichas, spec, budget, taxonomia=None):
    plan = planificar(taxonomia, fichas) if taxonomia is not None else None
    rutas = plan[1] if plan else {}
    structural, docs = estructura(corpus, fichas, rutas, taxonomia)
    origen, probes = configurar_sondas(spec, fichas, plan)
    with TemporaryDirectory() as tmp:
        db = Path(tmp) / "indice.sqlite"
        tick = perf_counter()
        brain.index(corpus, db)
        con, cfg, settings = brain.checked(db)
        index_time = round((perf_counter() - tick) * 1000)
        with closing(con):
            edges = defaultdict(set)
            for source, target in con.execute("SELECT source,target FROM edges"):
                edges[source].add(target)
            seen, queue = set(), ["index.md"]
            while queue:
                current = queue.pop()
                if current not in seen:
                    seen.add(current)
                    queue.extend(edges[current] - seen)
            structural["enlaces_resueltos"] = sum(map(len, edges.values()))
            structural["enlaces_sin_resolver"] = con.execute("SELECT count(*) FROM unresolved").fetchone()[0]
            structural["conceptos_sin_ruta_desde_indice"] = sorted(docs.keys() - seen)
            if plan:
                conteo_raiz = Counter(row[0] for row in con.execute("SELECT target FROM edges WHERE source='index.md'"))
                auditar_temas(corpus, plan, docs, conteo_raiz, structural)
            else:
                structural["grafo_tematico"] = {"estado": "formato_por_modulos"}

            def recuperar(queries):
                session = brain.session_load(None, cfg["revision"])
                return brain.pack(con, cfg, settings, session, queries, brain.Budget(budget), matched_sections=True)

            tick = perf_counter()
            batch = recuperar(list(dict.fromkeys(p["consulta"] for p in probes))) if probes else None
            casos = [
                {**probe, "en_lote": evaluar_sonda(probe, batch, docs, rutas),
                 "individual": evaluar_sonda(probe, recuperar([probe["consulta"]]), docs, rutas)}
                for probe in probes
            ]
    return structural, {
        "origen_pruebas": origen, "revision_indice": cfg["revision"], "version_motor": brain.VERSION,
        "presupuesto_caracteres": budget, "indexacion_ms": index_time,
        "sondas_ms": round((perf_counter() - tick) * 1000),
        "caracteres_paquete_en_lote": len(brain.dump(batch)) if batch else None,
        "fragmentos_en_lote": len(batch["passages"]) if batch else 0,
        "pendientes_del_motor_en_lote": batch["pending_total"] if batch else 0,
        "recuperadas_en_lote": sum(item["en_lote"]["estado"] == "recuperado" for item in casos),
        "recuperadas_individualmente": sum(item["individual"]["estado"] == "recuperado" for item in casos),
        "casos": casos,
    }
