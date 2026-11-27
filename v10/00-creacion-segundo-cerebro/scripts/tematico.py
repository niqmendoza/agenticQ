"""Planificar y renderizar un grafo de conceptos organizado por temas del producto."""

from collections import Counter, defaultdict
from posixpath import dirname, relpath

from fichas import texto
from okf import TIPOS_OKF, VERSION_OKF, cuerpo_atribuido, escribir, etiqueta_enlace, linea_enlace, texto_seguro
from repositorio import ID


def contexto(item, campos):
    if not isinstance(item, dict) or set(item) != campos | {"id", "titulo", "descripcion"}:
        raise ValueError("Cada área y MOC requiere id, titulo, descripcion y conceptos.")
    key = item["id"]
    if not isinstance(key, str) or not ID.fullmatch(key) or key in {"index", "log"}:
        raise ValueError("Usá IDs de área y MOC en minúsculas. index y log son nombres reservados.")
    descripcion = texto(item["descripcion"], 220, "descripcion")
    return key, texto(item["titulo"], 100, "titulo"), descripcion


def clave_referencia(value):
    if not isinstance(value, str) or len(parts := value.split("/")) != 2 or not all(ID.fullmatch(i) for i in parts):
        raise ValueError("Identificá cada concepto como modulo/id.")
    return value


def normalizar(value):
    return " ".join(value.casefold().split()).rstrip(".")


def planificar(datos, fichas):
    """Validar pertenencia exclusiva, descripciones y conexiones explícitas de cada nota."""
    if (
        not isinstance(datos, dict) or set(datos) != {"areas", "mocs"}
        or any(not isinstance(datos[k], list) or not datos[k] for k in ("areas", "mocs"))
    ):
        raise ValueError("La taxonomía requiere listas no vacías de areas y mocs.")
    notas = {
        f"{key}/{fact['id']}": fact for key, ficha in fichas.items() for fact in ficha["hechos"]
    }
    errores = []

    def incidencia(causa, **datos):
        errores.append({"causa": causa, **datos})

    areas, apariciones, rutas = [], Counter(), {}
    ids_areas = set()
    for item in datos["areas"]:
        key, title, description = contexto(item, {"conceptos"})
        if key in ids_areas:
            incidencia("area_duplicada", area=key)
        ids_areas.add(key)
        if not isinstance(item["conceptos"], list) or not item["conceptos"]:
            raise ValueError(f"El área {key} requiere al menos un concepto.")
        concepts = [clave_referencia(value) for value in item["conceptos"]]
        for concept in concepts:
            apariciones[concept] += 1
            if concept not in notas:
                incidencia("concepto_ausente", area=key, concepto=concept)
            else:
                rutas[concept] = f"temas/{key}/concepto-{notas[concept]['id']}.md"
        areas.append({"id": key, "titulo": title, "descripcion": description, "conceptos": concepts})
    for concept in sorted(notas):
        if apariciones[concept] != 1:
            incidencia("pertenencia_incorrecta", concepto=concept, apariciones=apariciones[concept])
    for ruta, count in Counter(rutas.values()).items():
        if count > 1:
            incidencia("ruta_duplicada", ruta=ruta)

    mocs, ids_mocs = [], set()
    for item in datos["mocs"]:
        key, title, description = contexto(item, {"conceptos"})
        if key in ids_mocs:
            incidencia("moc_duplicado", moc=key)
        ids_mocs.add(key)
        if not isinstance(item["conceptos"], list) or len(item["conceptos"]) < 2:
            raise ValueError(f"El MOC {key} requiere al menos dos conceptos.")
        concepts, vistos = [], set()
        for entry in item["conceptos"]:
            if not isinstance(entry, dict) or set(entry) != {"destino", "motivo"}:
                raise ValueError(f"Cada enlace del MOC {key} requiere destino y motivo.")
            dest = clave_referencia(entry["destino"])
            if dest not in notas:
                incidencia("concepto_ausente_en_moc", moc=key, destino=dest)
            if dest in vistos:
                incidencia("concepto_duplicado_en_moc", moc=key, destino=dest)
            vistos.add(dest)
            concepts.append({"destino": dest, "motivo": texto(entry["motivo"], 220, "motivo en MOC")})
        mocs.append({"id": key, "titulo": title, "descripcion": description, "conceptos": concepts})

    descripciones = defaultdict(list)
    salientes, entrantes = defaultdict(list), defaultdict(list)
    for key, nota in sorted(notas.items()):
        desc = normalizar(nota.get("descripcion", ""))
        tipo = normalizar(TIPOS_OKF[nota["tipo"]])
        if (
            not desc or desc == normalizar(nota["titulo"]) or desc == tipo
            or desc.startswith(tipo + " de ") and len(desc.split()) <= len(tipo.split()) + 3
        ):
            incidencia("descripcion_generica_o_ausente", concepto=key)
        else:
            descripciones[desc].append(key)
        if "estado" not in nota:
            incidencia("estado_ausente", concepto=key)
        vistos = set()
        for edge in nota.get("relaciones", []):
            dest = edge["destino"]
            if dest not in notas:
                incidencia("relacion_sin_destino", concepto=key, destino=dest)
                continue
            if "motivo" not in edge or edge["tipo"] == "relacionado con":
                incidencia("relacion_sin_justificacion_especifica", concepto=key, destino=dest)
                continue
            signature = (dest, edge["tipo"])
            if signature in vistos:
                incidencia("relacion_duplicada", concepto=key, destino=dest)
                continue
            vistos.add(signature)
            salientes[key].append(edge)
            entrantes[dest].append({**edge, "origen": key})
    for keys in descripciones.values():
        if len(keys) > 1:
            incidencia("descripcion_repetida", conceptos=keys)
    for key in sorted(notas):
        if not salientes[key] and not entrantes[key]:
            incidencia("concepto_aislado", concepto=key)
    return {"areas": areas, "mocs": mocs}, rutas, notas, salientes, entrantes, errores


def vinculo(origen, destino):
    return relpath(destino, dirname(origen) or ".")


def linea_relacion(edge, rutas, notas, origen, *, entrante=False):
    key = edge["origen"] if entrante else edge["destino"]
    verb = f"Recibe «{edge['tipo']}» de" if entrante else edge["tipo"]
    return f"* {verb} [{etiqueta_enlace(notas[key]['titulo'])}]({vinculo(origen, rutas[key])}) — {texto_seguro(edge['motivo'])}"


def publicar_tematico(bundle, mapa, taxonomia, rutas, notas, salientes, entrantes):
    (bundle / "mocs").mkdir(parents=True)
    app = mapa["app"]
    portada = [
        f"# {texto_seguro(app)}", "", "## Aplicación", "",
        linea_enlace("Aplicación", "aplicacion.md", "Vista general y commit de origen."), "",
        "## Mapas de contenido", "",
    ]
    area_links = []
    for moc in taxonomia["mocs"]:
        path = f"mocs/{moc['id']}.md"
        portada.append(linea_enlace(moc["titulo"], path, texto_seguro(moc["descripcion"])))
        escribir(bundle / path, [
            f"# {texto_seguro(moc['titulo'])}", "", texto_seguro(moc["descripcion"]), "",
            *[linea_enlace(notas[x["destino"]]["titulo"], vinculo(path, rutas[x["destino"]]), texto_seguro(x["motivo"]))
              for x in moc["conceptos"]],
        ], {"type": "Mapa de contenido", "title": moc["titulo"], "description": moc["descripcion"]})
    for area in taxonomia["areas"]:
        folder = bundle / "temas" / area["id"]
        folder.mkdir(parents=True)
        path = f"temas/{area['id']}/index.md"
        area_links.append(linea_enlace(area["titulo"], path, texto_seguro(area["descripcion"])))
        seccion = [f"## {texto_seguro(area['titulo'])}", "", texto_seguro(area["descripcion"]), ""]
        index = []
        for origin, lines in (("index.md", portada), (path, index)):
            lines.extend(["", *seccion])
            lines.extend(
                linea_enlace(notas[key]["titulo"], vinculo(origin, rutas[key]), texto_seguro(notas[key]["descripcion"]))
                for key in area["conceptos"]
            )
        escribir(folder / "index.md", index[1:])
    etiquetas = {
        "vigente": "Comportamiento documentado en el commit.",
        "planificado": "Planificación de una capacidad.",
        "historico": "Registro histórico.",
        "por-confirmar": "Información pendiente de confirmación.",
    }
    for key, nota in notas.items():
        body, sources = cuerpo_atribuido(nota, mapa["commit"])
        body = [f"**Estado del conocimiento** · {etiquetas[nota['estado']]}", "", *body]
        path = rutas[key]
        if salientes[key]:
            body += ["", "## Relaciones", "", *[linea_relacion(e, rutas, notas, path) for e in salientes[key]]]
        if entrantes[key]:
            body += ["", "## Referenciado por", "", *[linea_relacion(e, rutas, notas, path, entrante=True) for e in entrantes[key]]]
        escribir(bundle / path, body, {
            "type": TIPOS_OKF[nota["tipo"]], "title": nota["titulo"], "description": nota["descripcion"],
            "status": "draft", "tags": [rutas[key].split("/")[1], nota["tipo"]],
            "qa_estado": nota["estado"], "qa_concepto": key,
        }, sources)
    escribir(bundle / "aplicacion.md", [
        f"Commit documentado `{mapa['commit']}`.", "", "## Temas del producto", "", *area_links,
    ], {"type": "Aplicación", "title": app, "description": "Vista general y commit de origen.", "qa_commit": mapa["commit"]})
    escribir(bundle / "index.md", portada, {"okf_version": VERSION_OKF})
