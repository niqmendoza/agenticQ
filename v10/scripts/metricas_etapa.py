"""Calcular indicadores comparables desde los resultados locales de cada etapa."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile


def leer(path):
    if not path.is_file() or path.is_symlink():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}


def cortes_nativos(carpetas):
    cortes = {}
    registros = (leer(path) for carpeta in carpetas for path in carpeta.glob("consumo-*.json"))
    for corte in sorted(registros, key=lambda row: (
        row.get("corte_utc") or "", row.get("llamadas_unicas", 0), row.get("fuente_sha256") or "",
    )):
        if digest := corte.get("conversacion_sha256"):
            cortes[digest] = corte
    return list(cortes.values())


def total_observado(cortes, campo):
    values = [row.get(campo) for row in cortes]
    return sum(values) if values and None not in values else None


def indicadores(etapa, identifier):
    logs = etapa / "logs" / identifier
    salida = etapa / "salidas" / identifier
    res = sorted((leer(path) for path in logs.glob("*/resumen.json")), key=lambda row: row.get("inicio_utc") or "")
    inicio = [row["inicio_utc"] for row in res if row.get("inicio_utc")]
    fin = [row["fin_utc"] for row in res if row.get("fin_utc")]
    elapsed = (
        (datetime.fromisoformat(max(fin)) - datetime.fromisoformat(min(inicio))).total_seconds()
        if inicio and fin else None
    )
    cortes = cortes_nativos([logs])
    info = {
        "id": identifier,
        "intentos_script": len(res),
        "estados_script": dict(Counter(row["estado"] for row in res if "estado" in row)),
        "tiempo_script_s": round(sum(row.get("duracion_segundos", 0) for row in res), 3),
        "ventana_primero_a_ultimo_s": elapsed if elapsed is not None and elapsed >= 0 else None,
        "conversaciones_con_corte_nativo": len(cortes),
        "tokens_entrada_observados": total_observado(cortes, "tokens_entrada"),
        "tokens_salida_observados": total_observado(cortes, "tokens_salida"),
    }
    if etapa.name == "00-creacion-segundo-cerebro":
        campos = (
            "operacion", "commit", "archivos_indexados", "omisiones", "entradas", "caracteres_fuente",
            "modulo", "consultas", "fragmentos", "caracteres_fragmentos",
            "caracteres_contexto", "presupuesto_caracteres", "contexto_recortado", "caracteres_corpus",
            "redacciones", "hechos", "pendientes", "okf_version", "relaciones_pendientes",
            "modulos_reutilizables", "modulos_para_revisar",
            "modulos_reutilizados", "modulos_sin_revision",
            "estado_medicion", "contexto_publicado", "conceptos_de_qa",
            "recuperadas_en_lote", "pruebas_recuperacion",
        )
        info["trabajo_documental"] = [{k: row[k] for k in campos if k in row} for row in res]
        return info
    if etapa.name != "03-ejecuciones":
        invalid = Counter()
        for path in logs.glob("*/citas-invalidas.json"):
            invalid.update(row["causa"] for row in leer(path))
        info["citas_invalidas_por_causa"] = dict(invalid)
        if etapa.name == "01-analisis":
            info["redacciones_del_indice"] = sum(
                row["cantidad"] for path in logs.glob("*/indice.json")
                for row in leer(path).get("redacciones", [])
            )
        return info

    result = leer(salida / "dictamen.json")
    if not result:
        return info
    cases = result.get("casos", [])
    preflight = result["preflight"]
    groups = preflight.get("grupos_funcionales", {})
    blocked_by_technical = Counter()
    group_cases = {case for group in groups.values() if group.get("causa") for case in group["casos"]}
    for case_id, reason in preflight["bloqueos_por_caso"].items():
        if case_id not in group_cases:
            blocked_by_technical[reason] += 1
    causes = {}
    for row in cases:
        if row["attempts"] and row["status"] != "passed":
            amount = causes.setdefault(row.get("cause") or row["status"], {"casos": 0, "duracion_ms": 0})
            amount["casos"] += 1
            amount["duracion_ms"] += row["duration_ms"]
    info.update(
        intentos_casos=result["intentos"],
        reintentos_casos=sum(max(0, row["attempts"] - 1) for row in cases),
        casos_sin_intento=len(result.get("casos_sin_ejecutar", [])),
        causas_por_caso_con_intento=causes,
        bloqueos_previos_fuera_de_grupos=dict(blocked_by_technical),
        preflight_funcional_por_causa=dict(Counter(row["causa"] for row in groups.values() if row.get("causa"))),
        preflight_sesiones_probadas=sum(row["estado"] in {"listo", "bloqueado"} for row in groups.values()),
        preflight_duracion_ms=sum(row["duracion_ms"] for row in groups.values()),
        preflight_tecnico_ms=preflight.get("duracion_tecnica_ms"),
        retests_documentados=len(list(logs.glob("historial-retest*.json"))),
        **result.get("mediciones_motor", {}),
    )
    return info


def publicar(etapa, identifier):
    path = etapa / "logs" / identifier / "metricas-etapa.json"
    data = indicadores(etapa, identifier)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        tmp = Path(stream.name)
        try:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.close()
            tmp.replace(path)
        finally:
            tmp.unlink(missing_ok=True)
