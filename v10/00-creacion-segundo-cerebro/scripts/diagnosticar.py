"""Consolidar consumo nativo, navegación y recuperación del segundo cerebro."""

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from metricas_etapa import cortes_nativos, leer, total_observado
from soporte import abrir, huella, principal, read_json, run_id, write_json

from evaluar_okf import evaluar_lectura
from repositorio import SCHEMA

ETAPA = Path(__file__).resolve().parents[1]


def opciones(parser):
    parser.add_argument("--cerebro", required=True, type=Path)
    parser.add_argument("--corrida", type=run_id, help="Prefijo común de los IDs de la corrida.")
    parser.add_argument("--actividad", type=run_id, action="append", default=[], help="ID adicional. Se puede repetir.")
    parser.add_argument("--pruebas", type=Path, help="Consultas de QA con conceptos esperados.")
    parser.add_argument("--max-chars", type=int, default=16000)


def actividad(args, id_entrega, commit):
    logs = ETAPA / "logs"
    ids = {id_entrega, *args.actividad}
    if args.corrida and logs.is_dir():
        ids.update(path.name for path in logs.iterdir() if path.is_dir() and not path.is_symlink()
                   and (path.name == args.corrida or path.name.startswith(args.corrida + "-")))
    rows, incluidos, omitidos = [], [], []
    for key in sorted(ids - {args.id}):
        folder = logs / run_id(key)
        attempts = [
            entry for path in sorted(folder.glob("*/resumen.json"))
            if (entry := leer(path)) and entry.get("operacion") != "diagnosticar"
        ] if not folder.is_symlink() else []
        if not attempts:
            omitidos.append({"id": key, "causa": "sin_logs_de_actividad"})
            continue
        if any(row.get("commit") and row["commit"] != commit for row in attempts):
            omitidos.append({"id": key, "causa": "commit_distinto"})
            continue
        incluidos.append(folder)
        for row in attempts:
            campos = (
                "operacion", "modulo", "inicio_utc", "fin_utc", "codigo", "duracion_segundos",
                "consultas", "entradas", "fragmentos", "caracteres_fragmentos", "caracteres_contexto",
                "presupuesto_caracteres", "contexto_recortado", "caracteres_fuente", "archivos_indexados",
                "modulos_reutilizables", "modulos_reutilizados", "error",
            )
            rows.append({"id": key, **{field: row[field] for field in campos if field in row}})
    rows.sort(key=lambda row: (row.get("inicio_utc", ""), row["id"]))
    return rows, incluidos, omitidos


def consumo_registrado(dirs):
    cortes = cortes_nativos(dirs)
    inputs = total_observado(cortes, "tokens_entrada")
    outputs = total_observado(cortes, "tokens_salida")
    modelos = defaultdict(list)
    for corte in cortes:
        grupos = corte.get("por_modelo") or {
            "sin identificar": {
                "llamadas": corte["llamadas_unicas"], "tokens_entrada": corte["tokens_entrada"],
                "tokens_salida": corte["tokens_salida"],
            }
        }
        for model, grupo in grupos.items():
            modelos[model].append(grupo)
    return {
        "estado": "sin_medicion" if not cortes else "parcial" if None in (inputs, outputs) else "medido",
        "tokens_entrada": inputs, "tokens_salida": outputs,
        "tokens_total": inputs + outputs if None not in (inputs, outputs) else None,
        "tokens_cache_lectura": total_observado(cortes, "tokens_cache_lectura"),
        "llamadas_observadas": sum(corte["llamadas_unicas"] for corte in cortes),
        "conversaciones_medidas": len(cortes),
        "por_modelo": {
            model: {
                "llamadas": sum(row["llamadas"] for row in filas),
                "tokens_entrada": total_observado(filas, "tokens_entrada"),
                "tokens_salida": total_observado(filas, "tokens_salida"),
            }
            for model, filas in sorted(modelos.items())
        },
        "cortes": cortes,
    }


def navegacion(rows):
    navegadas = {row["id"] for row in rows if "caracteres_contexto" in row}
    fragmentos = Counter()
    casos_sin_resultados, filas_recortadas, contextos_sin_integridad = [], [], []
    caracteres = 0
    for key in sorted(navegadas):
        root = ETAPA / "salidas" / key
        receipt = leer(root / "entrega.json")
        archivos = receipt.get("archivos", {})
        path = root / ("contexto-qc.json" if "contexto-qc.json" in archivos else "contexto.json")
        expected = archivos.get(path.name)
        if path.is_symlink() or not path.is_file() or not expected or huella(path) != expected:
            contextos_sin_integridad.append(key)
            continue
        data = read_json(path)
        caracteres += len(path.read_text(encoding="utf-8"))
        if data.get("modo") == "buscar" and not data["entradas"]:
            casos_sin_resultados.append(key)
        if data.get("recortado") or data.get("evidencia_recortada"):
            filas_recortadas.append(key)
        for entry in data.get("entradas", data.get("evidencia", [])):
            if "texto" in entry:
                fragmentos[(entry["archivo"], entry["desde"], entry["hasta"], entry["texto"])] += 1
    return {
        "contextos_verificados": len(navegadas) - len(contextos_sin_integridad),
        "caracteres_contexto_publicado": caracteres,
        "fragmentos_publicados": sum(fragmentos.values()),
        "fragmentos_exactos_repetidos": sum(n - 1 for n in fragmentos.values()),
        "caracteres_de_fragmentos_repetidos": sum((n - 1) * len(k[-1]) for k, n in fragmentos.items()),
        "busquedas_sin_resultados": casos_sin_resultados,
        "contextos_recortados": filas_recortadas,
        "contextos_sin_integridad": contextos_sin_integridad,
    }


def escribir_reporte(path, report):
    tokens, nav, okf, lectura = (report[key] for key in ("consumo", "navegacion", "okf", "recuperacion"))

    def contador(value):
        return "Sin medición" if value is None else str(value)

    lines = [
        "# Diagnóstico de creación y consumo del segundo cerebro", "",
        f"- Aplicación · {report['app']}",
        f"- Commit · `{report['commit']}`",
        f"- Huella del corpus · `{report['corpus_sha256']}`",
        f"- IDs de actividad incluidos · {len(report['ids_actividad'])}", "",
        "## Uso de Copilot", "",
        f"- Estado del corte · {tokens['estado']}",
        f"- Entrada observada · {contador(tokens['tokens_entrada'])}",
        f"- Salida observada · {contador(tokens['tokens_salida'])}",
        f"- Llamadas observadas · {tokens['llamadas_observadas']}", "",
        "## Contexto publicado por los scripts", "",
        f"- Paquetes verificados · {nav['contextos_verificados']}",
        f"- Caracteres publicados · {nav['caracteres_contexto_publicado']}",
        f"- Fragmentos repetidos exactos · {nav['fragmentos_exactos_repetidos']}",
        f"- Búsquedas sin resultados · {len(nav['busquedas_sin_resultados'])}",
        f"- Paquetes recortados · {len(nav['contextos_recortados'])}", "",
        "## Bundle OKF y recuperación en la etapa 01", "",
        f"- Conceptos de QA · {okf['conceptos_de_qa']}",
        f"- Módulos con conceptos · {report['modulos_con_hechos']} de {len(report['modulos'])}",
        f"- Pendientes de documentación y relaciones · {report['pendientes']}",
        f"- Incidencias estructurales · {len(okf['incidencias'])}",
        f"- Conceptos sin ruta desde el índice · {len(okf['conceptos_sin_ruta_desde_indice'])}",
        f"- Evaluación del grafo temático · {okf['grafo_tematico']['estado']}",
        f"- Grupos con afirmaciones repetidas · {len(okf['afirmaciones_repetidas'])}",
        f"- Tipo de prueba de recuperación · {lectura['origen_pruebas']}",
        f"- Recuperados en lote · {lectura['recuperadas_en_lote']} de {len(lectura['casos'])}",
        f"- Recuperados como consultas independientes · {lectura['recuperadas_individualmente']} de {len(lectura['casos'])}",
        f"- Presupuesto de recuperación en caracteres · {lectura['presupuesto_caracteres']}", "",
        "El diagnóstico usa el recuperador de la etapa 01 con las consultas indicadas en el JSON adjunto.",
        "Las sondas por título comprueban acceso al contenido. Las consultas de QA miden recuperación frente a sus expectativas.",
    ]
    grafo = okf["grafo_tematico"]
    if "areas" in grafo:
        lines += [
            "", f"- Áreas y MOCs · {grafo['areas']} y {grafo['mocs']}",
            f"- Conceptos con una entrada en el índice raíz · {grafo['indice_raiz_unico']}",
            f"- Relaciones justificadas · {grafo['relaciones_justificadas']}",
            f"- Relaciones entre áreas · {grafo['relaciones_entre_areas']}",
            f"- Conceptos aislados · {len(grafo['conceptos_aislados'])}",
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def operar(args, salida, logs, resumen):
    """Publicar diagnóstico estructural y de consumo sin volver a consultar a un modelo."""
    resumen["operacion"] = "diagnosticar"
    if not 3000 <= args.max_chars <= 30000:
        raise ValueError("El presupuesto del diagnóstico debe estar entre 3000 y 30000 caracteres.")
    root = args.cerebro.resolve()
    receipt = abrir(root, ETAPA.name, requiere="manifiesto.json")
    manifest = read_json(root / "manifiesto.json")
    if manifest.get("schema") != SCHEMA or manifest.get("corpus") != "corpus" or not manifest.get("okf_version"):
        raise ValueError("Indicá una entrega OKF publicada por la etapa 00.")
    commit = manifest["commit"]
    resumen["commit"] = commit
    fichas = read_json(root / "fichas.json")
    spec = read_json(args.pruebas) if args.pruebas else None
    taxonomia = read_json(root / "taxonomia.json") if manifest.get("grafo", {}).get("organizacion") == "tematica" else None
    structural, retrieval = evaluar_lectura(root / "corpus", fichas, spec, args.max_chars, taxonomia)
    rows, dirs, omitted = actividad(args, receipt["id"], commit)
    nav, usage = navegacion(rows), consumo_registrado(dirs)
    report = {
        "schema": "agentic-qc/diagnostico-cerebro-1", "app": manifest["app"], "commit": commit,
        "okf_version": manifest["okf_version"], "entrega_sha256": huella(root / "entrega.json"),
        "corpus_sha256": hashlib.sha256(json.dumps(
            {k: v for k, v in receipt["archivos"].items() if k.startswith("corpus/")}, sort_keys=True,
        ).encode()).hexdigest(),
        "modulos": manifest["modulos"], "pendientes": manifest["pendientes"],
        "modulos_con_hechos": sum(row["hechos"] > 0 for row in manifest["modulos"].values()),
        "archivos_indexados": manifest["archivos_indexados"], "archivos_omitidos_por_causa": manifest["omisiones"],
        "ids_actividad": [folder.name for folder in dirs], "actividad_omitida": omitted,
        "duracion_script_s": round(sum(row.get("duracion_segundos", 0) for row in rows), 3),
        "actividad": rows, "consumo": usage, "navegacion": nav, "okf": structural, "recuperacion": retrieval,
    }
    write_json(salida / "diagnostico.json", report)
    escribir_reporte(salida / "diagnostico.md", report)
    resumen.update(
        estado_medicion=usage["estado"], contexto_publicado=nav["caracteres_contexto_publicado"],
        conceptos_de_qa=structural["conceptos_de_qa"], recuperadas_en_lote=retrieval["recuperadas_en_lote"],
        pruebas_recuperacion=len(retrieval["casos"]),
    )
    observado = (
        bool(retrieval["casos"]) and retrieval["recuperadas_en_lote"] == len(retrieval["casos"])
        and not structural["incidencias"] and not structural["conceptos_sin_ruta_desde_indice"]
        and (taxonomia is None or not structural["enlaces_sin_resolver"])
    )
    return 0 if observado else 3


if __name__ == "__main__":
    principal(__file__, opciones, operar)
