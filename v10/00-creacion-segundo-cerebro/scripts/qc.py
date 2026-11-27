"""Validar escenarios y producir las notas de QC del mismo corpus OKF."""

import re
from datetime import date

from fichas import comprobar_fuente, texto
from okf import escribir, linea_enlace, texto_seguro
from perfil_qc import contiene, id_qc
from soporte import abrir, read_json
from tematico import vinculo

REVISIONES = {"borrador", "revisado", "listo-para-qc", "bloqueado"}
ESCENARIO = {
    "id", "titulo", "tipo", "prioridad", "capa", "actor", "precondiciones", "configuracion",
    "datos_sinteticos", "accion", "resultado", "evidencia", "prueba", "ejecucion",
}


def textos(items, nombre):
    if not isinstance(items, list) or len(items) > 12:
        raise ValueError(f"{nombre}: usá una lista de hasta 12 textos.")
    return [texto(v, 280, nombre) for v in items]


def publicar_ref(value, mapa, db, cache):
    if not isinstance(value, dict) or set(value) - {"blob", "commit"} != {
        "id", "tipo", "archivo", "desde", "hasta", "localizador",
    }:
        raise ValueError("Cada fuente de resultado requiere id, tipo, archivo, rango y localizador.")
    identifier = id_qc(value["id"], "fuente")
    path = value["archivo"]
    if not isinstance(path, str):
        raise ValueError("Cada fuente requiere ruta.")
    fuentes = mapa["perfil_qc"]["fuentes"]
    match = max((p for p in fuentes if contiene(path, p)), key=len, default=None)
    if match is None or fuentes[match] != value["tipo"]:
        raise ValueError(f"Fuente sin autorización para el tipo declarado: {path}.")
    if path in cache and "blob" in value and cache[path][0] != value["blob"]:
        raise ValueError(f"Cambió el objeto citado: {path}.")
    cite = comprobar_fuente(value, db, cache)
    if value.get("blob", cite["blob"]) != cite["blob"]:
        raise ValueError(f"Cambió el objeto citado: {path}.")
    if value["tipo"] == "test":
        lines = cache[path][1][cite["desde"] - 1:cite["hasta"]]
        if not any(re.search(r"\b(?:assert\w*|expect\w*|require\w*|should\w*|Equal\w*)\b", line, re.I)
                   and not re.match(r"\s*(?:import\b|from\b|//|#)", line) for line in lines):
            raise ValueError(f"Citá un rango de test que incluya la comprobación: {path}.")
    return {"id": identifier, "tipo": value["tipo"], **cite, "commit": mapa["commit"]}


def ejecucion(value):
    if not isinstance(value, dict) or value.get("estado") not in {"no-ejecutado", "paso", "fallo"}:
        raise ValueError("La ejecución admite no-ejecutado, paso o fallo.")
    if value["estado"] == "no-ejecutado" and set(value) == {"estado"}:
        return value
    if value["estado"] == "no-ejecutado" or set(value) != {"estado", "entorno", "fecha", "registro"}:
        raise ValueError("Una ejecución observada requiere entorno, fecha y registro.")
    return {**value, "entorno": texto(value["entorno"], 120, "entorno"),
            "fecha": date.fromisoformat(value["fecha"]).isoformat(),
            "registro": texto(value["registro"], 220, "registro de ejecución")}


def escenario(value, mapa, db, cache, invalidaciones, anterior):
    if not isinstance(value, dict) or set(value) != ESCENARIO:
        raise ValueError("El escenario debe completar id, título, tipo, prioridad, capa, actor, precondiciones, configuración, datos sintéticos, acción, resultado, evidencia, prueba y ejecución.")
    key = id_qc(value["id"], "caso")
    if (
        value["tipo"] not in {"valido", "fallo"}
        or value["prioridad"] not in {"alta", "media", "baja"}
        or value["capa"] not in {"ui", "api", "integracion", "otra"}
    ):
        raise ValueError(f"{key}: tipo, prioridad o capa inválida.")
    result = {**value, "id": key}
    for field, maximum in (("titulo", 120), ("actor", 120), ("accion", 500), ("resultado", 500)):
        result[field] = texto(value[field], maximum, field)
    for field in ("precondiciones", "configuracion", "datos_sinteticos"):
        result[field] = textos(value[field], field)
    if not isinstance(value["evidencia"], list) or len(value["evidencia"]) > 4:
        raise ValueError(f"{key}: cada resultado admite hasta cuatro fuentes.")
    refs = {}
    for raw in value["evidencia"]:
        try:
            if not anterior and isinstance(raw, dict) and raw.get("commit", mapa["commit"]) != mapa["commit"]:
                raise ValueError(f"{key}: la fuente declara otro commit.")
            cite = publicar_ref(raw, mapa, db, cache)
        except ValueError as error:
            if not anterior:
                raise
            invalidaciones.append({"caso": key, "fuente": raw.get("archivo"), "motivo": str(error)})
            continue
        if cite["id"] in refs:
            raise ValueError(f"{key}: ID de fuente repetido.")
        refs[cite["id"]] = cite
    result["evidencia"] = list(refs.values())
    prueba = value["prueba"]
    if not isinstance(prueba, dict) or prueba.get("estado") not in {"candidato", "existente"}:
        raise ValueError(f"{key}: indicá prueba existente o candidato.")
    if prueba["estado"] == "existente":
        if set(prueba) != {"estado", "fuente", "selector"}:
            raise ValueError(f"{key}: una prueba existente requiere fuente y símbolo o selector.")
        selector = texto(prueba["selector"], 160, "selector o símbolo")
        if refs.get(prueba["fuente"], {}).get("tipo") != "test":
            if not anterior:
                raise ValueError(f"{key}: la prueba existente debe citar una fuente de tipo test.")
            prueba = {"estado": "candidato"}
        else:
            path = refs[prueba["fuente"]]["archivo"]
            if not any(selector.casefold() in line.casefold() for line in cache[path][1]):
                raise ValueError(f"{key}: el símbolo o selector no aparece en el test citado.")
            prueba = {**prueba, "selector": selector}
    elif set(prueba) != {"estado"}:
        raise ValueError(f"{key}: el candidato requiere solo su estado.")
    result["prueba"], result["ejecucion"] = prueba, ejecucion(value["ejecucion"])
    return result


def ficha(value, mapa, notas, db, cache, *, anterior=False, conceptos_cambiados=(), perfil_cambiado=False):
    required = {"id", "conceptos", "revision", "escenarios"}
    optional = {"sin_fallo_aplicable", "discrepancias", "invalidaciones"}
    if not isinstance(value, dict) or required - value.keys() or value.keys() - required - optional:
        raise ValueError("La ficha QC requiere id, conceptos, revision y escenarios.")
    key = id_qc(value["id"], "flujo")
    if key not in mapa["perfil_qc"]["flujos_criticos"]:
        raise ValueError(f"El flujo {key} debe figurar en el perfil.")
    links = textos(value["conceptos"], "conceptos")
    invalid = list(value.get("invalidaciones", [])) if anterior else []
    if perfil_cambiado:
        invalid.append({"motivo": "Cambió el alcance o riesgo del flujo crítico."})
    if len(set(links)) != len(links):
        raise ValueError(f"{key}: conceptos duplicados.")
    for target in links:
        if target not in notas:
            if not anterior:
                raise ValueError(f"{key}: concepto inexistente: {target}.")
            invalid.append({"concepto": target, "motivo": "Ya no está publicado."})
        elif target in conceptos_cambiados:
            invalid.append({"concepto": target, "motivo": "Cambió el contenido o soporte del concepto."})
    review = value["revision"]
    if not isinstance(review, dict) or review.get("estado") not in REVISIONES or set(review) - {"estado", "por", "commit", "motivo"}:
        raise ValueError(f"{key}: revisión inválida.")
    review = {**review}
    if "por" in review:
        review["por"] = texto(review["por"], 120, "responsable de revisión")
        if not isinstance(review.get("commit"), str) or not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", review["commit"]):
            raise ValueError(f"{key}: el responsable requiere un commit revisado.")
    if review["estado"] in {"revisado", "listo-para-qc"}:
        review["por"] = texto(review.get("por"), 120, "responsable de revisión")
        if not anterior and review.get("commit") != mapa["commit"]:
            raise ValueError(f"{key}: la revisión debe indicar el commit del mapa.")
    if review["estado"] == "bloqueado":
        review["motivo"] = texto(review.get("motivo"), 280, "motivo de bloqueo")
    if not isinstance(value["escenarios"], list) or len(value["escenarios"]) > 24:
        raise ValueError(f"{key}: usá hasta 24 escenarios por flujo.")
    cases = [escenario(s, mapa, db, cache, invalid, anterior) for s in value["escenarios"]]
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError(f"{key}: IDs de casos duplicados.")
    if invalid:
        review.update(estado="bloqueado", motivo="Cambió la evidencia o el concepto citado. Requiere revisión.")
    discrepancias = []
    for gap in value.get("discrepancias", []):
        if not isinstance(gap, dict) or set(gap) != {"descripcion", "versiones"}:
            raise ValueError(f"{key}: cada discrepancia requiere descripción y versiones.")
        versions = textos(gap["versiones"], "versiones en disputa")
        if len(versions) < 2:
            raise ValueError(f"{key}: identificá ambas versiones de la discrepancia.")
        discrepancias.append({"descripcion": texto(gap["descripcion"], 280, "discrepancia"), "versiones": versions})
    if discrepancias and review["estado"] != "bloqueado":
        raise ValueError(f"{key}: una discrepancia abierta requiere revisión bloqueada.")
    exemption = texto(value["sin_fallo_aplicable"], 250, "justificación") if "sin_fallo_aplicable" in value else None
    if review["estado"] == "listo-para-qc":
        tipos = {c["tipo"] for c in cases}
        if not links or "valido" not in tipos or ("fallo" not in tipos and not exemption):
            raise ValueError(f"{key}: para promoción se requiere concepto, caso válido y fallo o justificación.")
        for case in cases:
            if not any(ref["tipo"] in {"contrato", "test"} for ref in case["evidencia"]):
                raise ValueError(f"{key}/{case['id']}: la promoción requiere respaldo de contrato o test.")
    return {
        "id": key, "conceptos": links, "revision": review, "escenarios": cases,
        **({"sin_fallo_aplicable": exemption} if exemption else {}),
        **({"discrepancias": discrepancias} if discrepancias else {}),
        **({"invalidaciones": invalid} if invalid else {}),
    }


def preparar_fichas(paths, anterior, mapa, fichas, db, cache):
    notas = {f"{mod}/{h['id']}": h for mod, f in fichas.items() for h in f["hechos"]}
    revisadas = {}
    for path in paths:
        data = read_json(path)
        if not isinstance(data, list):
            raise ValueError("Cada archivo de fichas QC contiene una lista de flujos.")
        for raw in data:
            flow = ficha(raw, mapa, notas, db, cache)
            if flow["id"] in revisadas:
                raise ValueError(f"Ficha QC duplicada: {flow['id']}.")
            revisadas[flow["id"]] = flow
    if anterior and (anterior / "fichas-qc.json").is_file():
        abrir(anterior, "00-creacion-segundo-cerebro", requiere="fichas-qc.json")
        old = read_json(anterior / "perfil-qc.json")
        fichas_previas = read_json(anterior / "fichas.json")
        previo = {f"{mod}/{h['id']}": h for mod, f in fichas_previas.items() for h in f["hechos"]}
        cambios = {key for key in notas if notas[key] != previo.get(key)}
        for key, raw in read_json(anterior / "fichas-qc.json").items():
            if key in mapa["perfil_qc"]["flujos_criticos"] and key not in revisadas:
                revisadas[key] = ficha(
                    raw, mapa, notas, db, cache, anterior=True, conceptos_cambiados=cambios,
                    perfil_cambiado=old["flujos_criticos"].get(key) != mapa["perfil_qc"]["flujos_criticos"][key],
                )
    return dict(sorted(revisadas.items()))


def ruta_qc(key):
    return f"qc/{key}.md"


def etiqueta_fuente(case, ref):
    return f"{case['id']}:{ref['id']}"


def escribir_flujo(corpus, raw, meta, rutas):
    path = ruta_qc(raw["id"])
    sources = []
    review = raw["revision"]
    body = [f"**Flujo** · {raw['id']} · {review['estado']}", "", texto_seguro(meta["riesgo"])]
    if review.get("motivo"):
        body += ["", f"**Motivo de revisión** · {texto_seguro(review['motivo'])}"]
    if review.get("por"):
        body += ["", f"**Revisión** · {texto_seguro(review['por'])} · {texto_seguro(review['commit'])}"]
    for key in raw["conceptos"]:
        if key in rutas:
            body.append(linea_enlace(key, vinculo(path, rutas[key]), "Concepto del flujo."))
    if raw.get("sin_fallo_aplicable"):
        body += ["", f"Fallo no aplicable · {texto_seguro(raw['sin_fallo_aplicable'])}"]
    for gap in raw.get("discrepancias", []):
        body += ["", "**Discrepancia abierta** · " + texto_seguro(gap["descripcion"]),
                 *[f"* {texto_seguro(v)}" for v in gap["versiones"]]]
    for case in raw["escenarios"]:
        notas = []
        definiciones = []
        for ref in case["evidencia"]:
            label = etiqueta_fuente(case, ref)
            local = f"{ref['archivo']} L{ref['desde']}-L{ref['hasta']}"
            sources.append({"id": label, "resource": f"Git {ref['commit']} · {local}", "title": ref["tipo"]})
            notas.append(f"[^{label}]")
            definiciones.append(f"[^{label}]: {ref['tipo']} · {texto_seguro(local)} · {texto_seguro(ref['localizador'])}")
        body += [
            "", f"## Caso {case['id']}", "", texto_seguro(case["titulo"]), "",
            f"**Tipo · prioridad · capa** · {case['tipo']} · {case['prioridad']} · {case['capa']}",
            f"**Actor** · {texto_seguro(case['actor'])}",
        ]
        for field, title in (("precondiciones", "Precondiciones"), ("configuracion", "Configuración"), ("datos_sinteticos", "Datos sintéticos")):
            body.append(f"**{title}** · " + (" · ".join(map(texto_seguro, case[field])) or "Sin condiciones declaradas."))
        body += [
            f"**Acción** · {texto_seguro(case['accion'])}",
            f"**Resultado observable** · {texto_seguro(case['resultado'])} {' '.join(notas)}",
            f"**Prueba** · {case['prueba']['estado']}" + (f" · {texto_seguro(case['prueba']['selector'])}" if "selector" in case["prueba"] else ""),
            f"**Ejecución** · {case['ejecucion']['estado']}" + (
                " · " + " · ".join(texto_seguro(case["ejecucion"][k]) for k in ("entorno", "fecha", "registro"))
                if case["ejecucion"]["estado"] != "no-ejecutado" else ""
            ),
            "", *definiciones,
        ]
    escribir(corpus / path, body, {
        "type": "Flujo QC", "title": meta["titulo"], "description": meta["riesgo"],
        "status": "stable" if review["estado"] == "listo-para-qc" else "draft",
        "qa_flujo": raw["id"], "qa_revision": review["estado"],
    }, sources)


def publicar_qc(corpus, mapa, flujos, rutas):
    catalogo = mapa["perfil_qc"]["flujos_criticos"]
    (corpus / "qc").mkdir()
    portada = ["# " + texto_seguro(mapa["app"]), "",
               linea_enlace("Índice de conceptos y mapas", "index.md", "Navegación del producto."), "",
               "## Flujos críticos"]
    indice = ["# Flujos QC", ""]
    cobertura = {}
    for key, meta in catalogo.items():
        raw = flujos.get(key)
        coverage = raw["revision"]["estado"] if raw else "ausente"
        cobertura[key] = {"estado": coverage, "casos": len(raw["escenarios"]) if raw else 0}
        if not raw:
            portada.append(f"* {texto_seguro(meta['titulo'])} · Ficha pendiente.")
            continue
        escribir_flujo(corpus, raw, meta, rutas)
        portada.append(linea_enlace(meta["titulo"], ruta_qc(key), coverage))
        indice.append(linea_enlace(meta["titulo"], f"{key}.md", coverage))
    escribir(corpus / "inicio.md", portada, {"type": "Portada QC", "title": mapa["app"]})
    escribir(corpus / "qc/index.md", indice)
    with (corpus / "index.md").open("a", encoding="utf-8") as stream:
        stream.write("\n## Control de calidad\n\n" + linea_enlace("Entrada breve", "inicio.md", "Flujos críticos.") + "\n")
        stream.write(linea_enlace("Fichas QC", "qc/index.md", "Escenarios, revisión y evidencia.") + "\n")
    return cobertura


def inventario_migracion(path, flujos):
    raw = read_json(path)
    if not isinstance(raw, list):
        raise ValueError("El inventario de migración requiere una lista.")
    items, vistos = [], set()
    for item in raw:
        if (
            not isinstance(item, dict) or set(item) - {"destino"} != {"nota", "decision", "motivo"}
            or item["decision"] not in {"incorporada", "historica", "pendiente"}
        ):
            raise ValueError("Cada nota requiere nota, decision, motivo y destino cuando se incorpora.")
        nota = texto(item["nota"], 250, "nota previa")
        if nota in vistos:
            raise ValueError(f"Nota repetida en migración: {nota}.")
        vistos.add(nota)
        result = {"nota": nota, "decision": item["decision"], "motivo": texto(item["motivo"], 280, "motivo")}
        if "destino" in item:
            target = texto(item["destino"], 130, "destino")
            flujo, sep, caso = target.partition("/")
            if flujo not in flujos or (sep and not any(s["id"] == caso for s in flujos[flujo]["escenarios"])):
                raise ValueError(f"Destino de migración inexistente: {target}.")
            result["destino"] = target
        elif item["decision"] == "incorporada":
            raise ValueError(f"Indicá el flujo o caso que incorpora {nota}.")
        items.append(result)
    return items
