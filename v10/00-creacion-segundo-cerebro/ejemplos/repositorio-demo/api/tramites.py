def consultar_tramite():
    return {"registro": "QA-17", "estado": "en revisión", "fuente": "REG-17"}


def buscar_tramite(identificador):
    if identificador != "QA-17":
        return 404, {"error": "trámite ausente"}
    return 200, consultar_tramite()
