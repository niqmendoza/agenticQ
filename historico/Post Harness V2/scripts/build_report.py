#!/usr/bin/env python3
"""Genera un reporte HTML autónomo a partir de métricas observadas.

Uso: python3 scripts/build_report.py [--metrics evidencias/metrics.json]
No realiza mediciones ni completa valores faltantes con estimaciones.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
USAGE_KEYS = (
    "input_tokens", "cached_input_tokens", "output_tokens",
    "reasoning_output_tokens", "total_tokens",
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def number(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, (float, int)):
        return f"{value:,.2f}".rstrip("0").rstrip(".").replace(",", "_").replace(".", ",").replace("_", ".")
    return esc(value)


def delta(current: object, previous: object) -> str:
    if not isinstance(current, (int, float)) or not isinstance(previous, (int, float)) or previous == 0:
        return "Sin comparación disponible"
    change = (current / previous - 1) * 100
    direction = "menos" if change < 0 else "más" if change > 0 else "igual"
    return f"{number(abs(change))}% {direction} que la anterior"


def validate(data: dict) -> None:
    iterations = data.get("iterations")
    if not isinstance(iterations, list) or [item.get("id") for item in iterations] != ["full", "v1", "v2"]:
        raise ValueError("iterations debe incluir full, v1 y v2, en ese orden")
    for item in iterations:
        usage = item.get("usage") or {}
        for key in USAGE_KEYS:
            value = usage.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError(f"{item['id']}.{key} debe ser entero no negativo o null")
        for subset, total in (("cached_input_tokens", "input_tokens"), ("reasoning_output_tokens", "output_tokens")):
            if usage.get(subset) is not None and usage.get(total) is not None and usage[subset] > usage[total]:
                raise ValueError(f"{item['id']}: {subset} no puede superar {total}")
        if all(usage.get(k) is not None for k in ("input_tokens", "output_tokens", "total_tokens")) and usage["input_tokens"] + usage["output_tokens"] != usage["total_tokens"]:
            raise ValueError(f"{item['id']}: total debe ser entrada + salida")
    for key in ("changes", "coverage", "limitations"):
        if not isinstance(data.get(key, []), list):
            raise ValueError(f"{key} debe ser una lista")


def uncached(item: dict):
    usage = item.get("usage") or {}
    values = usage.get("input_tokens"), usage.get("cached_input_tokens")
    return None if None in values else values[0] - values[1]


def render(data: dict) -> str:
    validate(data)
    iterations = data["iterations"]
    cards = []
    bars = []
    table_rows = []
    docs = []
    max_total = max((item.get("usage", {}).get("total_tokens") or 0 for item in iterations), default=1) or 1
    max_documents = max((item.get("document_tokens") or 0 for item in iterations), default=1) or 1
    for i, item in enumerate(iterations):
        usage = item.get("usage") or {}
        total = usage.get("total_tokens")
        previous = iterations[i - 1].get("usage", {}).get("total_tokens") if i else None
        title = esc(item.get("title") or item["id"])
        label = "Referencia histórica" if i < 2 else "Nueva ejecución"
        comparison = "Punto de partida" if not i else delta(total, previous)
        cards.append(f'''<article class="metric-card c{i}"><div class="eyebrow">ITERACIÓN {i + 1} <span>{label}</span></div><h3>{title}</h3><div class="metric">{number(total)}</div><div class="unit">tokens totales nativos</div><div class="comparison">{comparison}</div><div class="mini"><span><b>{number(item.get('model_responses'))}</b> respuestas del modelo</span><span><b>{number(item.get('local_calls'))}</b> llamadas locales</span></div></article>''')
        segments = [("uncached", uncached(item)), ("cached", usage.get("cached_input_tokens")), ("output", usage.get("output_tokens"))]
        segments_html = "".join(f'<span class="{name}" style="width:{value/max_total*100:.5f}%" title="{esc({"uncached":"Entrada no cacheada", "cached":"Caché", "output":"Salida"}[name])}: {number(value)}"></span>' for name, value in segments if value is not None and value > 0)
        bars.append(f'<div class="bar-row"><div class="bar-caption"><span>{i+1}. {title}</span><strong>{number(total)}</strong></div><div class="bar-track" role="img" aria-label="{title}: {number(total)} tokens totales; entrada no cacheada {number(uncached(item))}; caché {number(usage.get("cached_input_tokens"))}; salida {number(usage.get("output_tokens"))}">{segments_html}</div></div>')
        table_rows.append(f'''<tr><th scope="row">{i+1}. {title}</th><td>{number(total)}</td><td>{number(usage.get('input_tokens'))}</td><td>{number(uncached(item))}</td><td>{number(usage.get('cached_input_tokens'))}</td><td>{number(usage.get('output_tokens'))}</td><td>{number(item.get('model_responses'))}</td><td>{number(item.get('local_calls'))}</td></tr>''')
        doc_tokens = item.get("document_tokens")
        width = doc_tokens / max_documents * 100 if doc_tokens is not None else 0
        docs.append(f'<div class="doc-row"><span>{i+1}. {title}</span><div class="doc-track"><i style="width:{width:.5f}%"></i></div><strong>{number(doc_tokens)}</strong></div>')
    changes = "".join(f'<article class="change"><h3>{esc(item.get("title", ""))}</h3><p><span>Antes</span>{esc(item.get("before", ""))}</p><p><span>Ahora</span>{esc(item.get("after", ""))}</p></article>' for item in data.get("changes", []))
    coverage_rows = "".join('<tr><th scope="row">' + esc(item.get("criterion", "")) + '</th>' + ''.join(f'<td><span class="state">{esc(item.get(key) if item.get(key) is not None else "Sin dato")}</span></td>' for key in ("full", "v1", "v2")) + '</tr>' for item in data.get("coverage", []))
    limitations = "".join(f'<li>{esc(item)}</li>' for item in data.get("limitations", []))
    quality = "".join(f'<div class="quality-item"><h3>{i+1}. {esc(item.get("title", item["id"]))}</h3><p>{esc(item.get("quality_note") or "Sin evaluación registrada.")}</p><p class="muted">Casos: {number(item.get("cases"))} · Documentos presentados: {number(item.get("documents_presented"))} · Duración: {number(item.get("seconds"))} s</p><p class="muted">Razonamiento incluido en salida: {number((item.get("usage") or {}).get("reasoning_output_tokens"))} tokens.</p></div>' for i, item in enumerate(iterations))
    integrity = "Conservado · hash verificado" if data.get("integrity_ok") is True else "Verificación no confirmada"
    return TEMPLATE.replace("@@CARDS@@", "".join(cards)).replace("@@BARS@@", "".join(bars)).replace("@@ROWS@@", "".join(table_rows)).replace("@@DOCS@@", "".join(docs)).replace("@@CHANGES@@", changes).replace("@@COVERAGE@@", coverage_rows).replace("@@LIMITATIONS@@", limitations).replace("@@QUALITY@@", quality).replace("@@INTEGRITY@@", integrity).replace("@@SHA@@", esc(data.get("v1_report_sha256", "No disponible")))


TEMPLATE = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>QA agentizada · Tres recorridos de contexto</title>
<style>
:root{--ink:#10253b;--muted:#526477;--line:#dce4e9;--paper:#f4f7f9;--orange:#b84316;--teal:#00796b;--blue:#315cbe;--radius:19px}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:#174da2;text-underline-offset:3px}button,a{touch-action:manipulation}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #f5a623;outline-offset:4px}.wrap{width:min(1190px,calc(100% - 48px));margin:auto}header{background:var(--ink);color:white;padding:42px 0 31px;position:relative;overflow:hidden}header:after{content:"";position:absolute;width:310px;height:310px;border:70px solid #ffffff05;border-radius:50%;right:-50px;top:-140px;pointer-events:none}.topline{display:flex;justify-content:space-between;gap:20px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#bdcedd}.topline a{color:#d9e8ff}h1{font-size:clamp(30px,4vw,49px);line-height:1.1;letter-spacing:-.04em;margin:24px 0 14px;max-width:820px}header p{color:#cfdae4;max-width:740px;margin:0}header .tag{display:inline-block;margin-top:24px;padding:5px 11px;border:1px solid #567087;border-radius:99px;font-size:12px}main{padding:26px 0 38px}.section-head{display:flex;justify-content:space-between;align-items:baseline;gap:16px;margin:30px 0 14px}h2{font-size:23px;letter-spacing:-.025em;margin:0}h3{margin:0;font-size:17px}.muted,.note{color:var(--muted);font-size:13px}.note{margin:12px 0 0}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}.metric-card{background:white;border:1px solid var(--line);border-top:4px solid var(--blue);padding:21px;border-radius:var(--radius)}.metric-card.c1{border-top-color:var(--orange)}.metric-card.c2{border-top-color:var(--teal)}.eyebrow{font-size:11px;letter-spacing:.08em;font-weight:800;color:var(--muted)}.eyebrow span{display:block;font-weight:400;letter-spacing:0;margin-top:3px}.metric-card h3{margin:15px 0 8px}.metric{font-size:clamp(27px,3.5vw,42px);font-weight:760;font-variant-numeric:tabular-nums;letter-spacing:-.045em;line-height:1.2}.unit{font-size:12px;color:var(--muted)}.comparison{font-size:13px;font-weight:650;margin:16px 0}.mini{border-top:1px solid var(--line);padding-top:12px;display:flex;flex-direction:column;gap:4px;font-size:12px;color:var(--muted)}.mini b{color:var(--ink);font-size:15px}.panel{border:1px solid var(--line);background:white;border-radius:var(--radius);padding:23px}.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:0 0 21px}.legend span:before{content:"";width:11px;height:11px;display:inline-block;background:var(--blue);border-radius:3px;margin-right:6px}.legend .l-cached:before{background:#b7c9e9}.legend .l-output:before{background:#e77c46}.bar-row{margin:17px 0}.bar-caption{display:flex;justify-content:space-between;font-size:13px;margin-bottom:6px;gap:16px}.bar-track{display:flex;height:27px;overflow:hidden;background:#edf1f5;border-radius:5px}.uncached{background:var(--blue)}.cached{background:#b7c9e9}.output{background:#e77c46}.table-scroll{overflow:auto;margin-top:20px}table{border-collapse:collapse;width:100%;font-size:12px;white-space:normal}th,td{padding:12px 10px;text-align:right;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}thead th{color:var(--muted);font-size:11px;font-weight:650;vertical-align:bottom}th:first-child{text-align:left;min-width:140px}tbody tr:last-child td,tbody tr:last-child th{border-bottom:0}.definition{padding:11px 14px;background:#f1f5fa;border-radius:9px;font-size:12px;color:#40566b;margin-top:16px}.docs{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:center}.docs h3{font-size:17px;margin-bottom:8px}.docs p{font-size:13px;color:var(--muted);margin:0}.doc-row{display:grid;grid-template-columns:120px 1fr 80px;align-items:center;gap:12px;font-size:12px;margin:10px 0}.doc-row strong{text-align:right}.doc-track{height:10px;border-radius:9px;background:#edf2f5;overflow:hidden}.doc-track i{display:block;background:#4c7f8b;height:100%;border-radius:9px}.flow-panel{background:#eaf0f4;padding:23px;border-radius:var(--radius)}.flow-toolbar{display:flex;justify-content:space-between;align-items:center;gap:18px;margin-bottom:18px}.flow-toolbar p{margin:0}.controls{display:flex;gap:8px}button{border:1px solid #acbac7;background:white;color:var(--ink);border-radius:9px;padding:8px 13px;font:600 13px system-ui;cursor:pointer}button.primary{background:var(--ink);color:white;border-color:var(--ink)}button:disabled{opacity:.5;cursor:default}.lanes{display:grid;gap:12px}.lane{display:grid;grid-template-columns:155px 1fr;gap:12px;align-items:center}.lane-title{font-size:13px}.lane-title b{display:block;font-size:15px}.steps{display:flex;gap:18px}.step{position:relative;flex:1;background:white;border:1px solid #b9c7d2;border-radius:11px;min-height:82px;padding:12px;font-size:12px;transition:background .15s,border-color .15s}.step:not(:last-child):after{content:"→";position:absolute;right:-16px;top:28px;color:#526477;font-weight:700}.step small{display:block;font-size:10px;font-weight:700;letter-spacing:.05em;margin-bottom:5px;color:#526477}.step.active{background:#ddf2eb;border-color:#00796b;box-shadow:0 0 0 1px #00796b}.step.pending{background:#f6f8fa;color:#738392;border-style:dashed}.step.active small{color:#006253}.flow-status{min-height:22px;margin:16px 0 0;font-size:13px;font-weight:600}.changes{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}.change{background:white;border:1px solid var(--line);border-radius:var(--radius);padding:20px}.change h3{margin-bottom:14px;font-size:16px}.change p{font-size:13px;margin:10px 0;color:var(--muted)}.change p span{font-size:10px;letter-spacing:.07em;text-transform:uppercase;display:block;font-weight:800;color:var(--ink);margin-bottom:3px}.coverage table{table-layout:fixed}.coverage th:first-child{width:28%}.coverage th,.coverage td{text-align:left;vertical-align:top}.state{display:block;border-left:3px solid #8aa2b3;background:#f3f6f8;padding:7px 9px;border-radius:0 6px 6px 0;font-size:12px}.coverage .note{margin-bottom:0}details{background:white;border:1px solid var(--line);border-radius:12px;margin-top:12px;padding:15px 18px}summary{font-weight:650;cursor:pointer}.quality-item{padding:15px 0;border-bottom:1px solid var(--line)}.quality-item:last-child{border:0}.quality-item p{font-size:13px}.limits{padding-left:20px;font-size:13px;color:var(--muted)}.limits li{margin:8px 0}.links{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0 5px}.links a{border:1px solid #b9c7d2;padding:9px 13px;border-radius:9px;background:white;text-decoration:none;font-size:13px;font-weight:600}footer{font-size:12px;color:var(--muted);padding:0 0 30px}.hash{overflow-wrap:anywhere;font-family:ui-monospace,monospace;font-size:11px}@media(max-width:850px){.cards{gap:9px}.metric-card{padding:16px}.docs{grid-template-columns:1fr}.changes{grid-template-columns:1fr 1fr}.lane{grid-template-columns:1fr}.lane-title b{display:inline;margin-right:8px}.steps{gap:16px}.step{padding:10px}.topline{font-size:10px}.coverage table{table-layout:auto;min-width:650px}}@media(max-width:600px){.wrap{width:calc(100% - 28px)}header{padding:26px 0}.topline{flex-direction:column;gap:7px}.cards{grid-template-columns:1fr}.metric-card{display:grid;grid-template-columns:1fr 1fr;column-gap:15px}.metric-card h3{grid-column:1;margin-top:8px}.metric-card .eyebrow{grid-column:1/-1}.metric{grid-column:2;grid-row:2/4;text-align:right;font-size:31px;align-self:center}.unit{grid-column:2;text-align:right}.comparison{grid-column:1;margin:7px 0}.mini{grid-column:1/-1;flex-direction:row;justify-content:space-between;margin-top:7px}.section-head{display:block}.section-head .muted{display:block;margin-top:5px}.panel,.flow-panel{padding:16px}.flow-toolbar{align-items:flex-start;flex-direction:column}.steps{display:grid;grid-template-columns:1fr 1fr;gap:10px}.step:not(:last-child):after{display:none}.step{min-height:80px}.lane+.lane{margin-top:13px;padding-top:15px;border-top:1px solid #cfdae3}.changes{grid-template-columns:1fr}.doc-row{grid-template-columns:100px 1fr 70px;gap:8px}.legend{gap:12px}.links{flex-direction:column}.links a{text-align:center}}@media(prefers-reduced-motion:reduce){*{transition:none!important}}@media print{header{background:white;color:#10253b}header p,.topline{color:#526477}.controls{display:none}.wrap{width:100%}.metric-card,.panel,.change,.flow-panel{break-inside:avoid}details{break-inside:avoid}.links{display:none}}
</style></head><body>
<header><div class="wrap"><div class="topline"><span>QA agentizada / Post Harness V2</span><a href="../Post%20Harness/reporte.html">Abrir el primer informe ↗</a></div><h1>Tres formas de llegar<br>al contexto de prueba.</h1><p>Lectura completa → scripts V1 → scripts V2. Consumo registrado, cambios y cobertura, en una misma vista.</p><span class="tag">Regresión exploratoria · dos brazos históricos + una nueva ejecución</span></div></header>
<main class="wrap">
<section aria-labelledby="native-title"><div class="section-head"><h2 id="native-title">01 / Tokens registrados</h2><span class="muted">Usage nativo del modelo · contexto acumulado</span></div><div class="cards">@@CARDS@@</div>
<div class="panel" style="margin-top:15px"><div class="legend" aria-hidden="true"><span>Entrada no cacheada</span><span class="l-cached">Entrada cacheada</span><span class="l-output">Salida</span></div>@@BARS@@<div class="table-scroll"><table><caption class="muted" style="text-align:left;margin-bottom:5px">Desglose nativo de cada recorrido</caption><thead><tr><th scope="col">Recorrido</th><th scope="col">Total</th><th scope="col">Entrada total</th><th scope="col">Entrada no cacheada</th><th scope="col">Caché</th><th scope="col">Salida</th><th scope="col">Respuestas modelo</th><th scope="col">Llamadas locales</th></tr></thead><tbody>@@ROWS@@</tbody></table></div><div class="definition">Total = entrada + salida. Caché está incluida en entrada; razonamiento está incluido en salida. No se suman por segunda vez. Una llamada local no equivale a una respuesta del modelo.<br>Se mide recuperar contexto y generar casos. Desarrollo, preparación y reporte se contabilizan aparte en el Markdown.</div></div></section>
<section aria-labelledby="docs-title"><div class="section-head"><h2 id="docs-title">02 / Contexto documental registrado</h2><span class="muted">Conteo de payloads · proxy separado del uso nativo</span></div><div class="panel docs"><div><h3>Menos texto no asegura menos consumo.</h3><p>Estos tokens cuentan payloads documentales registrados. V2 tuvo una elisión reportada y reparada con replay; es una métrica proxy. Las rondas, instrucciones y salidas también pesan en el recorrido completo. Preparación e indexación se explican por separado en el documento técnico.</p></div><div>@@DOCS@@</div></div></section>
<section aria-labelledby="flow-title"><div class="section-head"><h2 id="flow-title">03 / Cómo se obtiene el contexto</h2><span class="muted">Esquema ilustrativo del flujo; no reproduce una traza real</span></div><div class="flow-panel"><div class="flow-toolbar"><p class="muted">Avanzá un paso para comparar el trabajo de cada recorrido.</p><div class="controls"><button id="reset" type="button">Reiniciar</button><button id="next" class="primary" type="button">Siguiente paso →</button></div></div><div class="lanes">
<div class="lane"><div class="lane-title"><b>1. Lectura completa</b>Todo entra al modelo</div><div class="steps"><div class="step" data-step="1"><small>01 / ENTRADA</small>Leer todos los documentos</div><div class="step" data-step="2"><small>02 / MODELO</small>Encontrar reglas y excepciones</div><div class="step" data-step="3"><small>03 / PROPUESTA</small>Diseñar implementación y casos</div><div class="step" data-step="4"><small>04 / CONTROL</small>Contrastar fuentes y esperados</div></div></div>
<div class="lane"><div class="lane-title"><b>2. Scripts V1</b>Consulta y ampliación</div><div class="steps"><div class="step" data-step="1"><small>01 / QUERY</small>Buscar términos en el índice</div><div class="step" data-step="2"><small>02 / SHOW</small>Ampliar por archivo y líneas</div><div class="step" data-step="3"><small>03 / PROPUESTA</small>Integrar contexto y generar casos</div><div class="step" data-step="4"><small>04 / CONTROL</small>Verificar citas con nuevas lecturas</div></div></div>
<div class="lane"><div class="lane-title"><b>3. Scripts V2</b>Paquete y memoria</div><div class="steps"><div class="step" data-step="1"><small>01 / PAQUETE</small>Resolver varias consultas juntas</div><div class="step" data-step="2"><small>02 / RELACIONES</small>Agregar fuentes relacionadas con límites</div><div class="step" data-step="3"><small>03 / AMPLIACIÓN</small>Entregar sólo evidencia faltante</div><div class="step" data-step="4"><small>04 / CONTROL</small>Verificar citas en lote y cerrar casos</div></div></div>
</div><p class="flow-status" id="flow-status" role="status" aria-live="polite">Vista completa del proceso.</p><noscript><p class="note">La vista estática muestra todos los pasos. Los controles requieren JavaScript.</p></noscript></div></section>
<section aria-labelledby="changes-title"><div class="section-head"><h2 id="changes-title">04 / Qué cambió en V2</h2><a href="EXPLICACION.md" class="muted">Ver decisiones y arquitectura ↗</a></div><div class="changes">@@CHANGES@@</div></section>
<section aria-labelledby="coverage-title"><div class="section-head"><h2 id="coverage-title">05 / Cobertura y calidad</h2><span class="muted">Estados observados · sin puntaje agregado</span></div><div class="panel coverage"><div class="table-scroll" style="margin-top:0"><table><thead><tr><th scope="col">Criterio</th><th scope="col">1. Completa</th><th scope="col">2. V1</th><th scope="col">3. V2</th></tr></thead><tbody>@@COVERAGE@@</tbody></table></div><p class="note">Más casos no implica mejor calidad. Esta es una revisión documental: no se ejecutaron pruebas de la aplicación.</p></div><details><summary>Observaciones por recorrido y métricas auxiliares</summary>@@QUALITY@@</details></section>
<section aria-labelledby="scope-title"><div class="section-head"><h2 id="scope-title">06 / Alcance del resultado</h2></div><div class="panel"><p style="margin:0;font-size:14px"><strong>Comparación exploratoria, no ensayo causal ni estadístico.</strong> Los dos primeros recorridos provienen del ensayo anterior; V2 es una ejecución nueva. Las diferencias registradas no garantizan un ahorro universal ni equivalencia de calidad.</p><ul class="limits">@@LIMITATIONS@@</ul></div><details><summary>Integridad del primer informe: @@INTEGRITY@@</summary><p class="note">SHA-256 del HTML original registrado para comprobar que se conserva intacto:</p><p class="hash">@@SHA@@</p></details><nav class="links" aria-label="Documentación y evidencia"><a href="EXPLICACION.md">Explicación completa · Markdown</a><a href="evidencias/metrics.json">Métricas · JSON</a><a href="evidencias/">Evidencias locales</a><a href="README.md">Uso de los scripts V2</a><a href="../Post%20Harness/reporte.html">Informe original intacto</a></nav></section>
</main><footer class="wrap">Post Harness V2 · HTML autónomo, sin servicios externos. “—” indica un dato no disponible.</footer>
<script>
(()=>{let phase=0;const next=document.getElementById('next'),reset=document.getElementById('reset'),status=document.getElementById('flow-status');const labels=['Vista completa del proceso.','Paso 1 de 4: obtener la evidencia inicial.','Paso 2 de 4: localizar reglas y dependencias.','Paso 3 de 4: completar contexto y preparar casos.','Paso 4 de 4: verificar referencias y cerrar el análisis.'];function paint(){document.querySelectorAll('.step').forEach(el=>{const n=Number(el.dataset.step);el.classList.toggle('active',phase>0&&n===phase);el.classList.toggle('pending',phase>0&&n>phase)});status.textContent=labels[phase];next.disabled=phase===4;reset.disabled=phase===0;next.textContent=phase===4?'Recorrido completo':'Siguiente paso →'}next.addEventListener('click',()=>{phase=Math.min(4,phase+1);paint()});reset.addEventListener('click',()=>{phase=0;paint()});paint()})();
</script></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=ROOT / "evidencias" / "metrics.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reporte-v2.html")
    args = parser.parse_args()
    data = json.loads(args.metrics.read_text(encoding="utf-8"))
    report = render(data)
    if "@@" in report:
        raise ValueError("Quedaron marcadores de plantilla sin resolver")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"HTML generado: {args.output.resolve()}")


if __name__ == "__main__":
    main()
