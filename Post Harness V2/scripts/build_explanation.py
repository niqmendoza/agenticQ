#!/usr/bin/env python3
"""Construye el documento técnico a partir de mediciones y revisiones guardadas."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'evidencias'
def load(p):return json.loads((E/p).read_text())
def fmt(v):return f'{v:,}'.replace(',','.') if isinstance(v,int) else str(v)
def change(new,old):return f'{100*(new/old-1):+.2f}%' if old else 'sin denominador'
def main():
 m=load('metrics.json');v=load('validacion-comparativa.json');review=load('revision-calidad.json');nv=load('usage-v2.json');rows=m['iterations'];full,v1,v2=rows;prep=load('preparacion-usage-parcial.json') if (E/'preparacion-usage-parcial.json').exists() else None
 text='''# Post Harness V2 — explicación completa

Fecha de referencia del ensayo: 27/10/2026, America/Argentina/Buenos_Aires.

## 1. Qué se entregó y qué se preservó

El HTML `reporte-v2.html` es la vista breve y visual de tres recorridos: **1) lectura completa; 2) scripts V1; 3) scripts V2**. Este documento contiene decisiones, métricas y límites. La carpeta `../Post Harness` original se conservó sin modificaciones; el control compara sus archivos contra hashes tomados antes de empezar V2. No se construyó ni modificó OWUI ni el segundo cerebro. No se implementó la feature, MCP, embeddings o un harness nuevo.

La feature sigue siendo el mock **renovar acceso temporal a un File desde el chat**: identidad y lectura actuales, rama S3/local, TTL propuesto de 60–3600 segundos, errores seguros, ausencia de mutaciones prohibidas y UI con carreras, traducciones y temas. P1–P7 y criterios A–G se copiaron exactamente de la consigna original. Los contratos propuestos no se convierten en funcionalidad existente.

## 2. Diseño de la comparación

Se reutilizan los primeros turnos terminados de los dos evaluadores históricos, con sus artefactos congelados, y se agrega un evaluador V2 con `fork_turns=none`. No recibe resultados, reportes, código del recuperador ni conversación previa del coordinador. Sólo recibe consigna, modalidad V2 y salidas de su CLI. Puede ampliar sin un objetivo obligatorio de ahorro. Las cinco preguntas son las mismas, ahora resueltas en un paquete.

Esto es una **regresión exploratoria histórica**, no un ensayo causal, aleatorizado ni estadístico. El coordinador conoce la feature y las omisiones anteriores, por lo que el mock ya no es un holdout. El nuevo modo también cambia instrucciones de navegación y formato: no se puede atribuir toda diferencia a una única función Python. No se hizo un tercer brazo adicional de navegación manual por OKF-INDEX; aquí hay exactamente los tres recorridos solicitados.

Se calibró sólo con routing urlIdx y CSP desarrollo/OpenShift. Motor e instrucciones se congelaron antes de ejecutar la V2 sobre el mock; no se reoptimizaron usando sus casos finales. Las verificaciones sintéticas usan otros nombres/tecnologías y prueban mecanismos, no calidad de un modelo en otra aplicación.

El corpus conserva 80 Markdown, 170.573 bytes y 42.721 tokens sumados por archivo con o200k_base. Dos `.DS_Store` quedan excluidos. La revisión textual del índice coincide con la V1: `c738d86cba0e9fc395c3c8dc5aecf429fffdada4bf4572b0a0210d05343445e3`. Los hashes del snapshot incluyen otra estructura de inventario y por eso su firma global tiene otro valor; los 80 textos deben coincidir individualmente.

## 3. Consumo nativo registrado

Se suman deltas `usage` de respuestas con response_id único; los IDs se exportan hasheados. El último `turn_token_usage` sólo se usa como comprobación, no se suma otra vez. Entrada cacheada es subconjunto de entrada; razonamiento es subconjunto de salida. **Total = entrada + salida.** Se conserva el rango exacto de respuestas y tiempos de cada turno.

'''
 text+='| Métrica | 1 · Completa | 2 · V1 | 3 · V2 |\n|---|---:|---:|---:|\n'
 fields=[('Entrada total','input_tokens'),('Entrada cacheada (incluida)','cached_input_tokens'),('Entrada no cacheada','uncached'),('Salida total','output_tokens'),('Razonamiento (incluido)','reasoning_output_tokens'),('Total acumulado','total_tokens')]
 for label,key in fields:
  values=[r['usage']['input_tokens']-r['usage']['cached_input_tokens'] if key=='uncached' else r['usage'][key] for r in rows];text+='| '+label+' | '+' | '.join(fmt(x) for x in values)+' |\n'
 text+='\n| Actividad | Completa | V1 | V2 |\n|---|---:|---:|---:|\n'
 for label,key in [('Respuestas del modelo','model_responses'),('Procesos CLI locales','local_calls'),('Documentos con pasajes presentados','documents_presented'),('Segundos del turno observado','seconds'),('Casos documentales, sin puntaje de calidad','cases')]:text+='| '+label+' | '+' | '.join(fmt(r[key]) for r in rows)+' |\n'
 text+=f"\nVariación total V1 frente a completa: **{change(v1['usage']['total_tokens'],full['usage']['total_tokens'])}**; V2 frente a V1: **{change(v2['usage']['total_tokens'],v1['usage']['total_tokens'])}**; V2 frente a completa: **{change(v2['usage']['total_tokens'],full['usage']['total_tokens'])}**. Cada porcentaje usa como denominador el brazo que se nombra después de ‘frente a’.\n\n"
 text+=f"V2 usa {v2['model']} / {v2['effort']}; igualdad de modelo/esfuerzo observada entre los tres brazos: **{v['model_effort_equal']}**. No se dispone de semilla, temperatura, snapshot interno o control de carga. La duración es task_started→task_complete, incluyendo herramientas, razonamiento y escritura; no latencia pura de inferencia.\n\n"
 text+='Los números son telemetría nativa observada del harness, no una factura definitiva. Las categorías no pesan igual en facturación y aquí no se consultaron precios ni se convirtió a dinero. Las llamadas locales pueden agruparse en una sola herramienta y no equivalen a inferencias. Se excluyen del comparativo principal los turnos posteriores de aclaración; los históricos y sus límites están en la evidencia original.\n\n'
 text+='## 4. Payload documental registrado, medido una sola vez\n\n| Contexto documental CLI | Completa | V1 | V2 |\n|---|---:|---:|---:|\n| Tokens proxy o200k_base | '+' | '.join(fmt(r['document_tokens']) for r in rows)+' |\n\n'
 text+='Esto cuenta documentación y envolturas de recuperación que se presentaron, no todos los tokens de entrada acumulados. En V1, 21 comprobaciones procesaron JSON completo dentro de Python pero mostraron sólo encabezados; el conteo histórico usa esa presentación real, no todos los archivos intermedios. En V2 los resultados se registran sin filtrar por el evaluador; hubo una elisión de presentación reportada y reparada con replay, que limita identificar exactamente lo presentado desde archivos; las salidas de verify son control estructural y no se suman como contexto documental. El transcript exportado permite comprobar otras salidas, invocaciones y definiciones, pero no contiene el aviso de la elisión reportada. No se resta una cifra aproximada de tokens para fingir exactitud. El uso nativo sigue siendo el indicador acumulado principal.\n\n'
 text+=f"Se comprobaron **{v['unique_source_lines_v2']} líneas fuente únicas** presentadas por V2 y la coincidencia literal de los pasajes numerados. Aviso de truncamiento de terminal detectado en el registro: **{v['terminal_truncation_notice_in_recorded_outputs']}**. Las listas/rangos acotados por el propio script se declaran como pendientes y no se consideran leídos.\n\n"
 text+='El conteo de archivos usa tiktoken 0.14.0 / o200k_base como proxy, no como sustituto del tokenizer nativo. Un archivo formateado por Python puede contener espacios y claves que el modelo no generó literalmente; por eso sus tokens tampoco se identifican con salida nativa. Los contadores nativos incluyen el razonamiento y las sucesivas entradas con historia; no se reconstruyen sumando documentos una sola vez.\n\n'
 text+='## 5. Arquitectura y cambios implementados\n\n'
 for item in m['changes']:text+=f"### {item['title']}\n\nAntes: {item['before']}\n\nV2: {item['after']}\n\n"
 text+='''### Recorrido concreto del motor

1. `index` lee el corpus, conserva referencias y hashes y segmenta encabezados fuera de fences. Los demás textos se tratan por líneas. No se sigue un symlink ni se descarga una URL.
2. SQLite guarda documentos/fragmentos y deriva frecuencias, longitudes, document frequencies, encabezados y relaciones resueltas. Si nada cambió se reutiliza todo. Si cambia un texto se actualiza ese documento y se reconstruyen las estadísticas globales derivadas: no se promete actualización parcial de cada posting.
3. `pack` normaliza consultas y utiliza ranking léxico OR BM25, con los pesos de campos heredados. Alterna semillas de cada pregunta para evitar monopolio de una consulta. No añade sinónimos ni usa un LLM.
4. Añade un salto acotado de enlaces desde semillas; el soporte de varias semillas favorece candidatos y se atenúan hubs con mucho grado. No se presupone qué aplicación, stack o dominio tiene el corpus. Los límites no prueban que se hayan recuperado todas las reglas.
5. Unifica fuentes y devuelve texto literal numerado, mapa de secciones y cobertura. El presupuesto se verifica sobre la serialización que se imprime: caracteres y opcionalmente tokens. No se corta una línea a mitad ni se oculta un recorte. Puede quedar un bloque que no cabe: se declara y se permite rango menor/mayor presupuesto.
6. La sesión guarda intervalos **devueltos por la herramienta**, con la revisión del corpus. Esto evita duplicación entre consultas. No garantiza memoria del modelo ni que el harness haya mostrado stdout completo. Por eso existe `--replay` y se prohíbe filtrar sin registrar la transformación.
7. `show` distingue range_complete de document_complete; headings permite comprobar encabezados sin cuerpos, links pagina relaciones y verify controla citas/cobertura estructural en lote.

La verificación SHA256 completa sigue activa antes de cada operación: no se cambió por mtime solamente. Agrupar consultas reduce las veces que se recorre el corpus, sin debilitar esa comprobación. El motor sigue siendo CLI Python local, invocado desde el harness existente. Las sesiones se reemplazan de forma atómica, pero no incluyen bloqueo de concurrencia: una sesión por tarea, sin escritores simultáneos.

No se introdujo una lista de rutas OWUI, una ontología por backend/frontend ni reglas de accesibilidad hardcodeadas. El texto relacionado puede aportar esas reglas si está escrito; el script no las inventa ni garantiza detectarlas todas. `document_utils.py` es soporte interno derivado de V1 y `brain.py` es la interfaz pública.

## 6. Cobertura y calidad de los casos

La revisión es manual, por el coordinador y sin ciego. El validador comprueba rangos y exposición material; no demuestra que la cita respalde semánticamente un esperado. Las etiquetas A–G presentes tampoco constituyen una puntuación de cobertura. La cantidad de casos se muestra sólo para ubicar entregas.

'''
 for row in review['coverage']:text+=f"- **{row['criterion']}** — completa: {row['full']}; V1: {row['v1']}; V2: {row['v2']}.\n"
 text+='\n### Observaciones concretas de la revisión\n\n'
 for item in review.get('detailed_findings',[]):text+='- '+item+'\n'
 text+='\n## 7. Pruebas y controles de integridad\n\n'
 text+='''Las pruebas del navegador cubren corpus vacío/sin resultados; líneas numeradas fieles; deduplicación y replay; rango frente a documento completo; presupuestos de caracteres/tokens y pendientes; grafo genérico con otro stack; invalidación por hash y sesión; encabezados ignorando comentarios dentro de código; citas no entregadas; requisitos/decisiones abiertas; enlaces ambiguos/ausentes; escritura de logs fuera de la fuente; IDs estables. Son controles de los scripts, no pruebas de la aplicación ni del modelo.

'''
 text+=f"- Archivos originales V1 comprobados: {v['v1_files_checked']}; modificados: {v['v1_changed']}.\n- Entradas congeladas V2 modificadas: {v['frozen_inputs_changed']}.\n- Fuentes OWUI modificadas: {v['corpus_changed']}.\n- Extractos literales con diferencias: {v['literal_errors']}.\n- Sumatorias nativas coinciden con último contador de turno: {v['all_native_sums_match']}.\n- SHA256 del HTML original: `{m['v1_report_sha256']}`.\n\n"
 text+='La verificación visual del HTML incluye escritorio/móvil, controles del diagrama, cifras, ausencia de solicitudes externas y enlaces locales. Sus resultados y capturas están en `evidencias/verificacion-html.json` y `render-*.png`. La gráfica del flujo es ilustrativa: no finge observar decisiones internas ni representa una traza temporal exacta.\n\n'
 text+='## 8. Preparación frente a costo por tarea\n\nLa indexación y la verificación documental usan CPU local y no hacen llamadas LLM. Desarrollar el motor, diseñar el experimento y revisar el corpus sí demandan trabajo del coordinador; producir el HTML también. No se suman como si fueran costo por cada consulta futura ni se omiten de la contabilidad del experimento.\n\n'
 if prep:text+=f"Snapshot nativo de preparación V2 del coordinador antes del despacho: {fmt(prep['preparation_usage']['input_tokens'])} entrada + {fmt(prep['preparation_usage']['output_tokens'])} salida = {fmt(prep['preparation_usage']['total_tokens'])} tokens. El JSON guarda por separado coordinación/informe posteriores observados hasta la exportación; no es el total final del proyecto. La preparación del generador visual se registra aparte cuando existe su rollout.\n\n"
 if (E/'preparacion-diseno-usage.json').exists():
  design=load('preparacion-diseno-usage.json');known=[t for t in design['turns'] if t['model_responses']>0];total_design=sum(t['usage_sum']['total_tokens'] for t in known);text+=f'Preparación del generador visual: {fmt(total_design)} tokens nativos registrados en sus turnos con respuestas. Los contextos heredados sin registros no se interpretan como cero. Ver `evidencias/preparacion-diseno-usage.json`.\n\n'
 text+='La preparación V1 tenía su propio snapshot separado en el informe original. Para reutilización, los gastos de desarrollo/indexación no se repiten por tarea, pero pueden reaparecer revisión de corpus, cambios, ampliaciones y validación. No se extrapola el porcentaje de este mock a N tareas ni se calcula un punto de equilibrio monetario sin más datos.\n\n'
 text+='## 9. Limitaciones y siguiente validación\n\n'
 for item in review['limitations']:text+='- '+item+'\n'
 text+='\nLa siguiente validación útil sería fijar V2 y ensayarla en varias features nuevas y otro corpus, con criterios previos, evaluadores ciegos cuando sea posible y más de una repetición. También comparar con navegación manual por el índice existente. Este ensayo no ejecutó ninguna prueba sobre OWUI.\n\n'
 text+='''## 10. Evidencias y reproducción

- [Reporte visual](reporte-v2.html), [guía CLI](README.md) e [instrucción breve para Copilot](COPILOT-INSTRUCCIONES.md).
- [Métricas comparativas](evidencias/metrics.json), [uso nativo V2](evidencias/usage-v2.json), [conteo de transcript](evidencias/transcript-v2.json).
- [Protocolo](evidencias/protocolo-v2.md), [entradas congeladas](evidencias/congelado-pre-evaluacion.json), [modalidad](evidencias/modalidad-v2.md), [consigna común](evidencias/consigna-comun.md).
- [Resultado del evaluador](evidencias/evaluacion/resultado.json), [bitácora](evidencias/evaluacion/comportamiento.md), [congelado](evidencias/evaluacion/congelado.json), [verificador](evidencias/evaluacion/verificacion.json).
- [Revisión manual](evidencias/revision-calidad.json), [integridad y fidelidad](evidencias/validacion-comparativa.json), [pruebas finales](evidencias/tests-finales.txt), [verificación visual](evidencias/verificacion-html.json).
- [Informe original intacto](../Post%20Harness/reporte.html). Las fuentes están en su snapshot y se referencian por ruta/sección/líneas/hash.

```sh
# Desde Post Harness V2, con tiktoken en el intérprete para tests de presupuesto
"../Post Harness/.venv/bin/python" -m unittest discover -s tests -v
python3 scripts/build_report.py
python3 scripts/build_explanation.py
```

La medición nativa se reproduce con `collect_metrics.py --rollout RUTA_JSONL`, usando el entorno de medición y conservando las evidencias históricas vecinas. El formato del rollout local es evidencia de esta versión, no una API estable. El extractor guarda números y payloads permitidos; no copia texto system/developer ni razonamiento cifrado. En `MANIFIESTO.json` se listan hashes de los entregables.
'''
 (R/'EXPLICACION.md').write_text(text);print(str(R/'EXPLICACION.md'))
if __name__=='__main__':main()
