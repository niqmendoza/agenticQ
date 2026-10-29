#!/usr/bin/env python3
"""Build a portable HTML and Markdown report from saved retrieval evidence."""
import argparse
from datetime import datetime
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def number(value):
    return f'{value:,}'.replace(',', '.')


def build(initial, calibration, destination):
    d = json.loads((initial / 'summary.json').read_text())
    cal = json.loads((calibration / 'summary.json').read_text())
    profiles = d['profiles']
    ordered = [('local-v2', 'Scripts locales V2 · paquete inicial'),
               ('ragflow-5', 'RAGFlow · 5 fragmentos por consulta'),
               ('ragflow-10', 'RAGFlow · 10 fragmentos por consulta'),
               ('ragflow-5-directed', 'RAGFlow · 5 + ampliaciones dirigidas')]
    base = profiles['ragflow-5']
    extra = (profiles['ragflow-10']['client_tokens'] / base['client_tokens'] - 1) * 100
    overhead = (1 - base['text_tokens'] / base['client_tokens']) * 100
    checks = base['checks']
    limits = [
        'Son 14 señales documentales del mismo mock conocido. No son 14 pruebas ejecutadas sobre la aplicación ni una medición exhaustiva de cobertura.',
        'Las consultas dirigidas estaban prefijadas a partir de lo que sabíamos que faltaba. Esta prueba no demuestra que Copilot o un agente las descubran solos.',
        'El paquete inicial local y las cinco consultas de RAGFlow usan políticas distintas de selección y límites. Recuperan la misma cantidad de señales, pero no exactamente las mismas.',
        'Los tokens son un proxy o200k_base del contenido serializado. No son el consumo nativo de Copilot ni una factura; faltan generación, historial, reintentos y caché.',
        'Se repitieron dos veces las cinco consultas por perfil. Eso comprueba estabilidad en este entorno, sin demostrar rendimiento o robustez general.',
        'RAGFlow transforma tablas Markdown en HTML al indexar. No se deben inventar rangos de líneas originales para esos fragmentos.'
    ]
    md = ['# Pruebas de recuperación · RAGFlow local', '', '29 de octubre de 2026.', '',
          '**Resultado:** la API y la persistencia funcionan; la recuperación básica necesita ampliaciones para entregar contexto suficiente.', '',
          'Se conservaron 80 documentos y 143 fragmentos tras reiniciar Docker. Pasaron 27 tests automatizados, incluidos cinco controles nuevos para interpretar el evaluador.', '',
          '| Modalidad | Señales documentales | Tokens de salida del cliente (proxy) |',
          '|---|---:|---:|']
    for key, title in ordered:
        p = profiles[key]
        md.append(f'| {title} | {p["checks_matched"]}/{p["checks_total"]} | {number(p["client_tokens"])} |')
    md += ['', f'Subir de 5 a 10 fragmentos incrementó la salida un **{extra:.1f}%** y sólo sumó una señal. Las seis ampliaciones dirigidas completaron el checklist con 11 llamadas en total.', '',
           f'En la salida del cliente de cinco fragmentos, el texto documental suma {number(base["text_tokens"])} tokens proxy frente a {number(base["client_tokens"])} del JSON completo. La diferencia incluye metadatos, campos derivados y envolturas; no equivale a un ahorro ya implementado.', '',
           '## Reglas que faltaron en la consulta básica', '']
    md += [f'- {c["title"]}: `{c["document"]}`.' for c in checks if not c['matched']]
    md += ['', '## Consultas ajenas al dominio', '',
           '| Umbral | Consultas ajenas sin resultados | Señales de la aplicación |', '|---|---:|---:|']
    for p in cal['profiles']:
        md.append(f'| {p["threshold"]} | {p["controls_empty"]}/{p["controls_total"]} | {p["checks_matched"]}/{p["checks_total"]} |')
    md += ['', 'La similitud no garantiza que exista una respuesta. No se cambió el umbral de conexión: la calibración no mostró una solución suficiente.', '',
           '## Controles técnicos', '',
           '- API key inválida: rechazada con HTTP 401.',
           '- Dataset inexistente: error explícito, sin evidencia.',
           '- Servicio sin escuchar: error explícito, sin confundirlo con una búsqueda vacía.',
           '- Fragmentos devueltos: todos pertenecen al dataset y a los documentos cargados.',
           '- Repetición: mismos conjuntos de fragmentos en las cinco consultas, tanto con 5 como con 10 resultados.', '',
           '## Siguiente ajuste recomendado', '',
           'Preparar una capa de recuperación que amplíe sólo donde falta evidencia, reúna fuentes y evite repetir contenido. El formato de salida sigue pendiente; estas pruebas no lo fijan. El diseño de esa capa debe distinguir el documento encontrado de la regla efectivamente recuperada.', '',
           'También conviene evaluar el modelo de embeddings antes de reindexar: el adaptador Ollama inspeccionado envía documentos y consultas sin prefijos de tarea. La [documentación de Nomic](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) prescribe prefijos distintos para búsqueda y documentos. Es un posible factor, no una causa aislada en este ensayo. La implementación revisada pertenece a [RAGFlow v0.27.3](https://github.com/infiniflow/ragflow/blob/v0.27.3/rag/llm/embedding_model.py).', '',
           '## Límites de interpretación', '']
    md += ['- ' + item for item in limits]
    md += ['', '## Reproducir', '', 'Desde `Post Harness V2`:', '', '```sh',
           '"../Post Harness/.venv/bin/python" ragflow-local/evaluate_retrieval.py --out ragflow-local/pruebas/NUEVA-EJECUCION',
           '"../Post Harness/.venv/bin/python" ragflow-local/calibrate_retrieval.py --out ragflow-local/pruebas/NUEVA-CALIBRACION',
           '"../Post Harness/.venv/bin/python" -m unittest discover -s tests -v', '```', '',
           'Cada ejecución requiere una carpeta nueva. Conserva protocolo, solicitudes sin encabezados de autenticación, respuestas nativas, salida del cliente, paquete local y resumen. No sobrescribe las evidencias históricas.', '',
           f'Evidencias iniciales: `{initial.relative_to(ROOT)}`. Calibración: `{calibration.relative_to(ROOT)}`.', '']
    destination.with_suffix('.md').write_text('\n'.join(md))

    maximum = max(p['client_tokens'] for p in profiles.values())
    rows = ''.join(f'<tr><td>{escape(title)}</td><td>{p["checks_matched"]} / {p["checks_total"]}</td>'
                   f'<td><b>{number(p["client_tokens"])}</b><div class="track"><i style="width:{p["client_tokens"] / maximum * 100:.1f}%"></i></div></td></tr>'
                   for key, title in ordered for p in [profiles[key]])
    check_rows = ''.join('<tr><td>' + escape(c['title']) + '<small>' + escape(c['document']) + '</small></td>' +
                         ''.join(f'<td><span class="{"yes" if profiles[k]["checks"][i]["matched"] else "no"}">{"Presente" if profiles[k]["checks"][i]["matched"] else "Falta"}</span></td>' for k, _ in ordered) + '</tr>'
                         for i, c in enumerate(checks))
    threshold_rows = ''.join(f'<tr><td>{p["threshold"]}</td><td>{p["controls_empty"]} / {p["controls_total"]}</td><td>{p["checks_matched"]} / {p["checks_total"]}</td></tr>' for p in cal['profiles'])
    html = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>QA / ATI · Pruebas RAGFlow</title>
<style>
:root{{--bg:#001f23;--card:#00363b;--line:#006972;--ink:#effcfd;--muted:#b2d4d7;--cyan:#00a0ad;--pink:#e11f8f;--yellow:#d8bf70}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(ellipse at 90% 0,#004f5666,transparent 55%),var(--bg);color:var(--ink);font:16px/1.65 system-ui,sans-serif}}main{{max-width:1140px;margin:auto;padding:46px 28px 70px}}header{{border-top:3px solid var(--pink);padding-top:23px;margin-bottom:36px}}.brand{{letter-spacing:.16em;font-size:12px;font-weight:750;color:var(--muted)}}h1{{font-size:clamp(30px,5vw,52px);line-height:1.12;letter-spacing:-.04em;max-width:860px;margin:20px 0}}h2{{font-size:24px;letter-spacing:-.025em;margin:0 0 15px}}p{{max-width:900px;color:var(--muted)}}strong,b{{color:var(--ink)}}.date{{font-size:13px;color:var(--muted)}}.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin:28px 0}}.card,section{{border:1px solid var(--line);border-radius:16px;background:linear-gradient(125deg,#00363be6,#001f23e6);padding:24px}}.card b{{display:block;font-size:39px;line-height:1.3}}.card span{{font-size:14px;color:var(--muted)}}section{{margin:20px 0}}.notice{{padding:18px 21px;border-left:4px solid var(--yellow);background:#d8bf7011;border-radius:0 12px 12px 0;color:var(--ink)}}.ok{{border-left-color:var(--cyan)}}.scroller{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:15px 12px;border-bottom:1px solid #00697277;vertical-align:top;text-align:left}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.045em;color:var(--muted)}}small{{display:block;color:var(--muted);font-size:11px;margin-top:4px}}.track{{height:5px;background:#004f56;margin-top:10px;border-radius:4px;min-width:110px}}.track i{{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--pink));border-radius:4px}}.yes,.no{{font-size:12px;display:inline-block;border-radius:30px;padding:3px 9px;white-space:nowrap}}.yes{{color:#91f2dd;background:#00a0ad22}}.no{{color:var(--yellow);background:#d8bf701a}}.steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.step{{border:1px dashed var(--line);padding:18px;border-radius:12px}}.step b{{display:block;color:var(--yellow)}}.step p{{font-size:14px;margin-bottom:0}}summary{{cursor:pointer;font-weight:650;padding:8px 0}}li{{margin:8px 0;color:var(--muted)}}a{{color:#7ee8f0}}footer{{color:var(--muted);font-size:13px;padding-top:18px}}.technical{{font-size:13px}}@media(max-width:720px){{main{{padding:24px 16px}}.cards,.steps{{grid-template-columns:1fr}}section{{padding:18px}}.card b{{font-size:30px}}.detail-table{{min-width:850px}}}}@media print{{body{{background:white;color:#123}}p,li,small,.date,footer,.brand{{color:#345}}b,strong,h1,h2{{color:#123}}section,.card{{background:white;border-color:#abc;break-inside:avoid}}.yes{{color:#165}}.no{{color:#765}}}}
</style></head><body><main>
<header><div class="brand">QA / ATI · LABORATORIO LOCAL</div><h1>La API funciona.<br>El contexto todavía necesita criterio.</h1><p>Comparamos el segundo cerebro local con RAGFlow usando las cinco consultas del ensayo anterior, el mismo corpus y un checklist de información que QA necesita encontrar.</p><div class="date">29 de octubre de 2026 · Ensayo exploratorio sobre un caso conocido</div></header>
<div class="cards"><div class="card"><b>80 / 80</b><span>documentos conservados y procesados</span></div><div class="card"><b>143</b><span>fragmentos indexados en RAGFlow</span></div><div class="card"><b>27</b><span>tests automatizados aprobados</span></div></div>
<p class="notice ok">Conectividad, autenticación y persistencia comprobadas. Los 14 puntos de la comparación siguiente son <strong>señales documentales</strong>, no pruebas ejecutadas sobre la aplicación.</p>
<section><h2>Más resultados no siempre traen mejores reglas</h2><div class="scroller"><table><thead><tr><th>Modalidad</th><th>Señales presentes</th><th>Tokens de salida del cliente · proxy</th></tr></thead><tbody>{rows}</tbody></table></div><p>Duplicar los fragmentos agregó una señal y aumentó el texto un <strong>{extra:.1f}%</strong>. Las ampliaciones dirigidas recuperaron los 14 puntos con seis consultas adicionales previamente definidas.</p><p class="technical">El paquete local inicial y RAGFlow recuperan ocho señales, pero no las mismas. Las políticas de selección difieren. Los resultados no prueban equivalencia de calidad.</p></section>
<section><h2>La respuesta también trae texto repetido y metadatos</h2><p>En RAGFlow con cinco fragmentos, los textos documentales suman <strong>{number(base['text_tokens'])}</strong> tokens proxy; la salida completa del cliente suma <strong>{number(base['client_tokens'])}</strong>. Los campos derivados, las envolturas y los metadatos amplían lo que recibiría el modelo.</p><p>Es una oportunidad para el futuro adaptador. Todavía no implementamos el formato de salida ni medimos ahorro real en Copilot.</p></section>
<section><h2>Qué información apareció en cada modalidad</h2><p>Se exige el documento correspondiente y las marcas de contenido del checklist. Una mención o enlace desde un índice no cuenta como recuperar la regla.</p><div class="scroller"><table class="detail-table"><thead><tr><th>Señal documental</th><th>Local V2</th><th>RAGFlow 5</th><th>RAGFlow 10</th><th>5 + ampliaciones</th></tr></thead><tbody>{check_rows}</tbody></table></div></section>
<section><h2>Una consulta ajena también puede traer resultados</h2><p>Probamos cuatro preguntas fuera del tema, incluidas situaciones ficticias. Con la configuración actual, las cuatro devolvieron fragmentos de la aplicación que no responden lo preguntado.</p><div class="scroller"><table><thead><tr><th>Umbral de similitud</th><th>Consultas ajenas sin resultados</th><th>Señales de la aplicación conservadas</th></tr></thead><tbody>{threshold_rows}</tbody></table></div><p class="notice">Subir el umbral no resolvió el problema: con 0.3 aún quedaron dos controles ajenos con resultados y se perdió una señal pertinente. Conservamos la configuración inicial.</p></section>
<section><h2>Controles técnicos comprobados</h2><ul><li>Credencial inválida: HTTP 401.</li><li>Dataset inexistente y servicio no disponible: errores explícitos.</li><li>Todos los fragmentos recibidos pertenecen al dataset y al corpus cargados.</li><li>Los conjuntos de fragmentos se mantuvieron al repetir las cinco consultas con 5 y con 10 resultados.</li><li>Los 80 documentos permanecieron disponibles después de reiniciar Docker.</li></ul></section>
<section><h2>Cómo seguimos a partir de esta evidencia</h2><div class="steps"><div class="step"><b>01 · Comprobar suficiencia</b><p>Distinguir encontrar un documento de recibir el fragmento que contiene la regla.</p></div><div class="step"><b>02 · Ampliar lo que falta</b><p>Hacer consultas dirigidas y conservar las dudas cuando no haya respaldo.</p></div><div class="step"><b>03 · Preparar el contexto</b><p>Reunir las fuentes y evitar repeticiones antes de entregarlo a Copilot.</p></div></div><p>El formato de salida se definirá después. También conviene evaluar los prefijos de consulta/documento del modelo de embeddings: la <a href="https://huggingface.co/nomic-ai/nomic-embed-text-v1.5">documentación de Nomic</a> los diferencia. El <a href="https://github.com/infiniflow/ragflow/blob/v0.27.3/rag/llm/embedding_model.py">adaptador Ollama inspeccionado</a> no los agrega; no aislamos su efecto en estas pruebas.</p></section>
<section><details><summary>Alcance, límites y evidencia conservada</summary><ul>{''.join('<li>'+escape(item)+'</li>' for item in limits)}</ul><p class="technical">Se guardaron protocolos, solicitudes sin credenciales, respuestas nativas, salida del cliente, índice y paquete local de la comparación y resúmenes JSON. No se ejecutó generación de casos ni se alteraron las evidencias históricas.</p></details></section>
<footer>HTML autónomo: incluye sus estilos y toda la comparación. Sin dependencias externas para consultar el reporte.</footer>
</main></body></html>'''
    destination.with_suffix('.html').write_text(html)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initial', type=Path, default=ROOT / 'pruebas/2026-10-29-inicial')
    parser.add_argument('--calibration', type=Path, default=ROOT / 'pruebas/2026-10-29-calibracion')
    parser.add_argument('--out', type=Path, default=ROOT / 'Pruebas-RAGFlow')
    args = parser.parse_args()
    build(args.initial, args.calibration, args.out)
    print('Reportes HTML autónomo y Markdown generados con las evidencias guardadas.')


if __name__ == '__main__':
    main()
