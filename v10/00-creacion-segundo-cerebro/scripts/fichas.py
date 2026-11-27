"""Validación y reutilización de fichas funcionales con referencias al código."""

from higiene import sanear
from indice import archivo
from okf import TIPOS_OKF
from repositorio import ID, SCHEMA
from soporte import abrir, read_json

RELACIONES = {
    "depende de", "usa", "valida", "documenta", "relacionado con", "limita",
    "controla", "implementa", "produce", "consume", "persiste en", "autoriza",
    "configura", "observa",
}
ESTADOS = {"vigente", "planificado", "historico", "por-confirmar"}


def texto(valor, maximo, field):
    if (
        not isinstance(valor, str) or not valor.strip() or len(valor) > maximo
        or len(valor.splitlines()) != 1 or sanear(valor)[1]
    ):
        raise ValueError(f"{field}: usá una línea de hasta {maximo} caracteres, sin valores sensibles.")
    return valor.strip()


def comprobar_fuente(ref, db, cache):
    path = ref.get("archivo")
    if not isinstance(path, str):
        raise ValueError("La cita necesita una ruta del índice.")
    if path not in cache:
        row = archivo(db, path)
        cache[path] = (row["oid"], row["texto"].split("\n"))
    oid, lines = cache[path]
    a, b = ref.get("desde"), ref.get("hasta")
    if type(a) is not int or type(b) is not int or not 1 <= a <= b <= len(lines) or b - a >= 40:
        raise ValueError(f"Rango inválido en {path}. Usá hasta 40 líneas.")
    locator = texto(ref.get("localizador"), 220, "localizador")
    if "[REDACTADO]" in locator or locator.casefold() not in "\n".join(lines[a - 1:b]).casefold():
        raise ValueError(f"El localizador literal no aparece en {path} L{a}-L{b}.")
    return {"archivo": path, "desde": a, "hasta": b, "localizador": locator, "blob": oid}


def validar(ficha, modulo, db, cache):
    if (
        not isinstance(ficha, dict) or ficha.get("modulo") != modulo
        or set(ficha) != {"modulo", "hechos", "pendientes"}
        or not isinstance(ficha["hechos"], list) or len(ficha["hechos"]) > 36
        or not isinstance(ficha["pendientes"], list) or len(ficha["pendientes"]) > 24
    ):
        raise ValueError(f"{modulo}: usá una ficha por módulo con hechos y pendientes como listas.")
    hechos, vistos = [], set()
    for hecho in ficha["hechos"]:
        required = {"id", "tipo", "titulo", "afirmacion", "evidencia"}
        if not isinstance(hecho, dict) or set(hecho) - {"relaciones", "descripcion", "estado"} != required:
            raise ValueError(f"{modulo}: cada hecho requiere id, tipo, título, afirmación y evidencia.")
        key = hecho["id"]
        if not isinstance(key, str) or not ID.fullmatch(key) or key in vistos or hecho["tipo"] not in TIPOS_OKF:
            raise ValueError(f"{modulo}: ID o tipo inválido, o ID de hecho duplicado.")
        vistos.add(key)
        refs = hecho["evidencia"]
        if not isinstance(refs, list) or not 1 <= len(refs) <= 3:
            raise ValueError(f"{modulo}/{key}: cada hecho requiere de una a tres citas.")
        citas = []
        for ref in refs:
            if not isinstance(ref, dict) or set(ref) - {"archivo", "desde", "hasta", "localizador", "blob"}:
                raise ValueError(f"{modulo}/{key}: referencia mal formada.")
            try:
                cita = comprobar_fuente(ref, db, cache)
            except ValueError as error:
                raise ValueError(f"{modulo}/{key}: {error}") from None
            if cita not in citas:
                citas.append(cita)
        if "estado" in hecho and hecho["estado"] not in ESTADOS:
            raise ValueError(f"{modulo}/{key}: estado de conocimiento inválido.")
        hechos.append({
            "id": key, "tipo": hecho["tipo"],
            "titulo": texto(hecho["titulo"], 100, "titulo"),
            "afirmacion": texto(hecho["afirmacion"], 600, "afirmacion"),
            "evidencia": citas,
            **({"descripcion": texto(hecho["descripcion"], 220, "descripcion")} if "descripcion" in hecho else {}),
            **({"estado": hecho["estado"]} if "estado" in hecho else {}),
            **({"relaciones": validar_relaciones(hecho["relaciones"], modulo, key)} if "relaciones" in hecho else {}),
        })
    pendientes = list(dict.fromkeys(texto(item, 300, "pendiente") for item in ficha["pendientes"]))
    if not hechos and not pendientes:
        raise ValueError(f"{modulo}: registrá un hecho con evidencia o un pendiente concreto.")
    return {"modulo": modulo, "hechos": hechos, "pendientes": pendientes}


def validar_relaciones(relaciones, modulo, key):
    if not isinstance(relaciones, list) or len(relaciones) > 8:
        raise ValueError(f"{modulo}/{key}: relaciones admite hasta ocho vínculos.")
    result = []
    for edge in relaciones:
        if (
            not isinstance(edge, dict) or set(edge) - {"motivo"} != {"tipo", "destino"}
            or edge["tipo"] not in RELACIONES or not isinstance(edge["destino"], str)
        ):
            raise ValueError(f"{modulo}/{key}: vínculo inválido.")
        target = edge["destino"].split("/")
        if len(target) != 2 or not all(ID.fullmatch(item) for item in target) or target == [modulo, key]:
            raise ValueError(f"{modulo}/{key}: el vínculo requiere otro concepto en formato modulo/id.")
        if "motivo" in edge:
            edge = {**edge, "motivo": texto(edge["motivo"], 220, "motivo de la relación")}
        if edge not in result:
            result.append(edge)
    return result


def reusar(anterior, mapa, db):
    if anterior is None:
        return {}, None
    root = anterior.resolve()
    abrir(root, "00-creacion-segundo-cerebro", requiere="manifiesto.json")
    old = read_json(root / "manifiesto.json")
    if old.get("schema") != SCHEMA or old.get("app") != mapa["app"]:
        raise ValueError("Indicá un segundo cerebro anterior de la misma aplicación y versión del esquema.")
    previous = read_json(root / "fichas.json")
    base = old["commit"]
    modules = mapa["modulos"]
    old_modules = old["modulos"]
    changed = {key for key in modules.keys() | old_modules.keys()
               if modules.get(key, {}).get("huella") != old_modules.get(key, {}).get("huella")}
    if old["configuracion"] != mapa["configuracion"] or old.get("huella_raiz") != mapa["huella_raiz"] or "raiz" in changed:
        return {}, base
    # Una modificación invalida también a los módulos que declaran depender de ella.
    invalid = set(changed)
    while True:
        additions = {key for key, meta in modules.items() if invalid.intersection(meta["depende_de"])}
        if additions <= invalid:
            break
        invalid.update(additions)

    reusable = {}
    for key, ficha in previous.items():
        if key in invalid or key not in modules or not ficha["hechos"]:
            continue
        refs = [ref for hecho in ficha["hechos"] for ref in hecho["evidencia"]]
        for ref in refs:
            row = db.execute("SELECT oid FROM archivos WHERE ruta=?", (ref["archivo"],)).fetchone()
            if row is None or row["oid"] != ref["blob"]:
                break
        else:
            reusable[key] = ficha
    return reusable, base
