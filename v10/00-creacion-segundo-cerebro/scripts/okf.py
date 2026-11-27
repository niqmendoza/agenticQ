"""Publicar un bundle OKF v0.2 con conceptos y relaciones de QA."""

import hashlib
import json
from html import escape

VERSION_OKF = "0.2"
TIPOS_OKF = {
    "flujo": "Flujo de aplicación",
    "regla": "Regla funcional",
    "interfaz": "Interfaz",
    "dato": "Dato",
    "prueba": "Prueba",
    "operacion": "Operación",
}


def texto_seguro(value):
    return escape(value, quote=False).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def etiqueta_enlace(value):
    return escape(value, quote=False).replace("[", "&#91;").replace("]", "&#93;")


def linea_enlace(titulo, destino, descripcion):
    return f"* [{etiqueta_enlace(titulo)}]({destino}) - {descripcion}"


def escribir(path, lines, metadata=None, sources=()):
    if metadata is not None:
        # JSON de una línea es YAML válido. Permite serializar valores sin sumar dependencias.
        frontmatter = [
            f"{key}: {json.dumps(value, ensure_ascii=False, allow_nan=False)}"
            for key, value in metadata.items()
        ]
        if sources:
            frontmatter.append("sources:")
            frontmatter.extend(
                f"  - {json.dumps(source, ensure_ascii=False, allow_nan=False)}" for source in sources
            )
        lines = ["---", *frontmatter, "---", "", *lines]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def ruta_modulo(key):
    return f"modulos/{key}/modulo.md"


def ruta_concepto(key, identifier):
    return f"modulos/{key}/concepto-{identifier}.md"


def fuente_okf(ref, commit):
    path, start, end = ref["archivo"], ref["desde"], ref["hasta"]
    title = f"{path} · L{start}-L{end}"
    key = hashlib.sha256(title.encode("utf-8")).hexdigest()[:12]
    return {
        "id": f"codigo-{key}", "title": title,
        "resource": f"Repositorio Git local, commit {commit}, {title}",
    }


def cuerpo_atribuido(hecho, commit):
    por_id = {}
    for ref in hecho["evidencia"]:
        source = fuente_okf(ref, commit)
        por_id[source["id"]] = source
    sources = list(por_id.values())
    footnotes = " ".join(f"[^{source['id']}]" for source in sources)
    return [
        f"{texto_seguro(hecho['afirmacion'])} {footnotes}", "",
        *(f"[^{source['id']}]: {texto_seguro(source['title'])}" for source in sources),
    ], sources


def escribir_concepto(bundle, key, hecho, commit, conceptos):
    body, sources = cuerpo_atribuido(hecho, commit)
    pendientes = []
    if relaciones := hecho.get("relaciones", []):
        body += ["", "## Relaciones", ""]
        for relacion in relaciones:
            destino, tipo = relacion["destino"], relacion["tipo"]
            if target := conceptos.get(destino):
                path, title = target
                motivo = f" — {texto_seguro(relacion['motivo'])}" if "motivo" in relacion else ""
                body.append(f"* {tipo} [{texto_seguro(title)}](/{path}){motivo}")
            else:
                pendientes.append({"origen": f"{key}/{hecho['id']}", **relacion})
                body.append(f"* Pendiente de vincular «{tipo}» a `{destino}`.")
    escribir(bundle / ruta_concepto(key, hecho["id"]), body, {
        "type": TIPOS_OKF[hecho["tipo"]], "title": hecho["titulo"],
        "description": hecho.get("descripcion", f"{TIPOS_OKF[hecho['tipo']]} de {key}."),
        "status": "draft", "tags": [key, hecho["tipo"]],
    }, sources)
    return pendientes


def publicar_okf(bundle, mapa, fichas):
    (bundle / "modulos").mkdir(parents=True)
    app = mapa["app"]
    modulos = ["# Módulos", ""]
    componentes = ["## Componentes", ""]
    conceptos = {
        f"{key}/{hecho['id']}": (ruta_concepto(key, hecho["id"]), hecho["titulo"])
        for key, ficha in fichas.items() for hecho in ficha["hechos"]
    }
    pendientes = []
    for key, ficha in sorted(fichas.items()):
        carpeta = bundle / "modulos" / key
        carpeta.mkdir()
        cobertura = f"{len(ficha['hechos'])} conceptos, {len(ficha['pendientes'])} pendientes de documentación."
        modulos.append(linea_enlace(key, f"{key}/", cobertura))
        componentes.append(linea_enlace(key, f"/{ruta_modulo(key)}", "Módulo de la aplicación."))
        index = [f"# {key}", "", linea_enlace(f"Módulo {key}", "modulo.md", "Vista general y dependencias.")]
        body = []
        if ficha["hechos"]:
            body += ["## Conceptos", ""]
            for hecho in ficha["hechos"]:
                titulo = hecho["titulo"]
                descripcion = f"{TIPOS_OKF[hecho['tipo']]} de {key}."
                path = ruta_concepto(key, hecho["id"])
                index.append(linea_enlace(titulo, path.rsplit("/", 1)[-1], descripcion))
                body.append(linea_enlace(titulo, f"/{path}", descripcion))
                pendientes.extend(escribir_concepto(bundle, key, hecho, mapa["commit"], conceptos))
        deps = [dep for dep in mapa["modulos"][key]["depende_de"] if dep in fichas]
        if deps:
            body += ["", "## Dependencias", ""]
            body.extend(f"* Depende de [{dep}](/{ruta_modulo(dep)})" for dep in deps)
        if ficha["pendientes"]:
            body += ["", "## Pendientes de confirmar", ""]
            body.extend(f"* {texto_seguro(item)}" for item in ficha["pendientes"])
        escribir(carpeta / "modulo.md", body, {
            "type": "Módulo de aplicación", "title": key, "tags": ["modulo"],
            **({"status": "draft"} if ficha["pendientes"] else {}),
        })
        escribir(carpeta / "index.md", index)
    escribir(bundle / "modulos/index.md", modulos)
    escribir(bundle / "aplicacion.md", [
        f"Commit documentado `{mapa['commit']}`.", "", *componentes,
    ], {
        "type": "Aplicación", "title": app, "description": "Vista general y commit de origen.",
        "qa_commit": mapa["commit"],
    })
    escribir(bundle / "index.md", [
        f"# {texto_seguro(app)}", "",
        linea_enlace("Aplicación", "aplicacion.md", "Vista general y commit de origen."),
        linea_enlace("Módulos", "modulos/", "Conceptos agrupados por módulo."),
    ], {"okf_version": VERSION_OKF})
    return pendientes
