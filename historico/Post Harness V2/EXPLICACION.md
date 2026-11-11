# Post Harness V2 — explicación completa

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

| Métrica | 1 · Completa | 2 · V1 | 3 · V2 |
|---|---:|---:|---:|
| Entrada total | 1.367.118 | 1.239.741 | 988.434 |
| Entrada cacheada (incluida) | 1.289.728 | 1.161.984 | 941.440 |
| Entrada no cacheada | 77.390 | 77.757 | 46.994 |
| Salida total | 16.037 | 18.510 | 16.242 |
| Razonamiento (incluido) | 1.881 | 2.650 | 1.950 |
| Total acumulado | 1.383.155 | 1.258.251 | 1.004.676 |

| Actividad | Completa | V1 | V2 |
|---|---:|---:|---:|
| Respuestas del modelo | 21 | 21 | 16 |
| Procesos CLI locales | 16 | 52 | 23 |
| Documentos con pasajes presentados | 80 | 27 | 28 |
| Segundos del turno observado | 376.21 | 406.583 | 440.334 |
| Casos documentales, sin puntaje de calidad | 38 | 29 | 38 |

Variación total V1 frente a completa: **-9.03%**; V2 frente a V1: **-20.15%**; V2 frente a completa: **-27.36%**. Cada porcentaje usa como denominador el brazo que se nombra después de ‘frente a’.

V2 usa gpt-6.1-sol / high; igualdad de modelo/esfuerzo observada entre los tres brazos: **True**. No se dispone de semilla, temperatura, snapshot interno o control de carga. La duración es task_started→task_complete, incluyendo herramientas, razonamiento y escritura; no latencia pura de inferencia.

Los números son telemetría nativa observada del harness, no una factura definitiva. Las categorías no pesan igual en facturación y aquí no se consultaron precios ni se convirtió a dinero. Las llamadas locales pueden agruparse en una sola herramienta y no equivalen a inferencias. Se excluyen del comparativo principal los turnos posteriores de aclaración; los históricos y sus límites están en la evidencia original.

## 4. Payload documental registrado, medido una sola vez

| Contexto documental CLI | Completa | V1 | V2 |
|---|---:|---:|---:|
| Tokens proxy o200k_base | 57.652 | 42.496 | 32.195 |

Esto cuenta documentación y envolturas de recuperación que se presentaron, no todos los tokens de entrada acumulados. En V1, 21 comprobaciones procesaron JSON completo dentro de Python pero mostraron sólo encabezados; el conteo histórico usa esa presentación real, no todos los archivos intermedios. En V2 los resultados se registran sin filtrar por el evaluador; hubo una elisión de presentación reportada y reparada con replay, que limita identificar exactamente lo presentado desde archivos; las salidas de verify son control estructural y no se suman como contexto documental. El transcript exportado permite comprobar otras salidas, invocaciones y definiciones, pero no contiene el aviso de la elisión reportada. No se resta una cifra aproximada de tokens para fingir exactitud. El uso nativo sigue siendo el indicador acumulado principal.

Se comprobaron **1607 líneas fuente únicas** presentadas por V2 y la coincidencia literal de los pasajes numerados. Aviso de truncamiento de terminal detectado en el registro: **False**. Las listas/rangos acotados por el propio script se declaran como pendientes y no se consideran leídos.

El conteo de archivos usa tiktoken 0.14.0 / o200k_base como proxy, no como sustituto del tokenizer nativo. Un archivo formateado por Python puede contener espacios y claves que el modelo no generó literalmente; por eso sus tokens tampoco se identifican con salida nativa. Los contadores nativos incluyen el razonamiento y las sucesivas entradas con historia; no se reconstruyen sumando documentos una sola vez.

## 5. Arquitectura y cambios implementados

### Paquete multiconsulta

Antes: El agente ejecutaba consultas separadas y elegía qué ampliar.

V2: Una operación combina preguntas y equilibra candidatos por consulta.

### Memoria por intervalos

Antes: Las relecturas no distinguían evidencia ya entregada.

V2: La sesión devuelve sólo líneas faltantes; replay permite releer explícitamente.

### Fuentes compactas

Antes: Se repetían rutas, metadatos crudos y campos derivados.

V2: Una tabla de fuentes por paquete y texto numerado con límites claros.

### Relaciones acotadas

Antes: Seguir enlaces dependía de cada decisión del agente.

V2: Un salto automático y candidatos pendientes visibles, sin reglas específicas de OWUI.

### Verificador en lote

Antes: El agente organizó 21 relecturas para revisar encabezados.

V2: Rangos, entrega, requisitos y pendientes se verifican en lote; el significado sigue requiriendo revisión.

### Índice con derivados persistidos

Antes: Cada query recalculaba estadísticas y resolvía enlaces por resultado.

V2: SQLite conserva ranking, encabezados y grafo; SHA256 sigue validando cambios.

### Recorrido concreto del motor

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

- **Identidad y permisos** — completa: Núcleo + duda write/read; V1: Núcleo + duda write/read; V2: Núcleo + pendiente explícito.
- **TTL y validación** — completa: Bordes y ambiguos separados; V1: Bordes; null/60.0 en dudas; V2: Bordes; null/60.0 pendientes.
- **S3, local y carreras** — completa: Cubierto; consistencia abierta; V1: Cubierto; consistencia abierta; V2: Cubierto; consistencia abierta.
- **Efectos laterales** — completa: Éxito/error + P4 abierto; V1: Matriz de error incompleta; V2: Éxito/error + P4 abierto.
- **Accesibilidad UI** — completa: AA 4,5:1/3:1 explícito; V1: Faltó fuente AA; V2: Fuente AA; explicitar umbral.
- **Fuentes y oráculos** — completa: Citas válidas; dudas en texto; V1: Citas válidas; dudas en texto; V2: 193 citas; 9 pendientes marcados.
- **Duplicados exactos** — completa: 0; V1: 0; V2: 0.

### Observaciones concretas de la revisión

- V2 C01–C11 recuperan identidad, pending, propietario/admin, None, {}, concesiones custom y cambios vigentes. C08 conserva write→read como pendiente Q02. Los códigos 403/404 se califican como propuestos, pero Q05 sobre ocultamiento no se enlaza con open_questions en todos los casos afectados (C06/C07/C17/C18): queda un límite de la verificación estructural.
- V2 C12–C15 cubren default, 60/3600, 59/3601, fracciones/bool/texto y objeto exacto. C14 marca 60.0 pendiente Q09 sin convertir esa interpretación en regla existente. C38 hace explícita la decisión null y TTL local. Agrupar muchas variantes no agrega un punto de calidad por cada valor.
- V2 C16–C27 distinguen URL previa, revocación, falta de registro frente a falta física, rama local protegida, fallback no garantizado y carreras. Los contratos de consistencia siguen pendientes; no se afirma que firmar compruebe existencia o garantice atomicidad.
- V2 C28 incluye revisión del camino de éxito y rechazo/error para efectos prohibidos. C29 no fija last_accessed_at ni promete extender retención; conserva Q01. Esto hace explícita una matriz que V1 C18 dejaba más acotada.
- V2 F15/C36 citan ECO Design System y el evaluador recibió su cuerpo, incluida la fila con AA 4,5:1/3:1. Se reparó la omisión de recuperación de V1. Sin embargo, C36 sólo dice mantener WCAG AA documentada: conviene escribir los valores concretos en el esperado antes de convertirlo en una prueba implementable. El baseline C35 sí los explicitaba.
- Los 38 casos V2 no prueban equivalencia con los 38 del baseline: las particiones difieren. Providers GCS/Azure quedan en Q08 sin un caso equivalente al C38 condicional del baseline; la distinción de adjunto type=chat del baseline tampoco se desarrolla como caso propio. No son requisitos P1–P7 nuevos por defecto, pero muestran cobertura adicional que no conviene borrar de la revisión.
- La validación final informa 193 citas con rangos válidos y devueltos, P1–P7 y etiquetas A–G presentes, cero duplicados exactos y nueve casos ligados a preguntas abiertas. C32 también tiene kind=inferencia y se incluye entre diez casos para revisión; tener nueve marcas pendientes no significa que sólo existan nueve inferencias.
- El evaluador informó una elisión de aproximadamente 152 tokens en la presentación del primer pack y la reparó con show 32–60 --replay del documento afectado. El aviso no aparece en los payloads de rollout exportados; no se puede deducir de ellos que la presentación estuvo libre de elisiones. El conteo documental V2 de 32.195 usa payloads CLI registrados e incluye la relectura: es un proxy, con esa limitación de presentación. El usage nativo acumulado se obtiene de contadores independientes y no se corrige restando una cifra aproximada.
- La V2 redujo total nativo 20,15% frente a V1 y entrada no cacheada de 77.757 a 46.994. El turno observado duró 440,334 s frente a 406,583 s en V1: no se demostró menor latencia. Cada brazo tiene una sola ejecución.

## 7. Pruebas y controles de integridad

Las pruebas del navegador cubren corpus vacío/sin resultados; líneas numeradas fieles; deduplicación y replay; rango frente a documento completo; presupuestos de caracteres/tokens y pendientes; grafo genérico con otro stack; invalidación por hash y sesión; encabezados ignorando comentarios dentro de código; citas no entregadas; requisitos/decisiones abiertas; enlaces ambiguos/ausentes; escritura de logs fuera de la fuente; IDs estables. Son controles de los scripts, no pruebas de la aplicación ni del modelo.

- Archivos originales V1 comprobados: 462; modificados: [].
- Entradas congeladas V2 modificadas: [].
- Fuentes OWUI modificadas: [].
- Extractos literales con diferencias: [].
- Sumatorias nativas coinciden con último contador de turno: True.
- SHA256 del HTML original: `69062ba62e54fae4c6128b73b61b32be88eeb9bdc95dc9a0156e8e1f1a1ccc68`.

La verificación visual del HTML incluye escritorio/móvil, controles del diagrama, cifras, ausencia de solicitudes externas y enlaces locales. Sus resultados y capturas están en `evidencias/verificacion-html.json` y `render-*.png`. La gráfica del flujo es ilustrativa: no finge observar decisiones internas ni representa una traza temporal exacta.

## 8. Preparación frente a costo por tarea

La indexación y la verificación documental usan CPU local y no hacen llamadas LLM. Desarrollar el motor, diseñar el experimento y revisar el corpus sí demandan trabajo del coordinador; producir el HTML también. No se suman como si fueran costo por cada consulta futura ni se omiten de la contabilidad del experimento.

Snapshot nativo de preparación V2 del coordinador antes del despacho: 2.439.219 entrada + 18.366 salida = 2.457.585 tokens. El JSON guarda por separado coordinación/informe posteriores observados hasta la exportación; no es el total final del proyecto. La preparación del generador visual se registra aparte cuando existe su rollout.

Preparación del generador visual: 285.841 tokens nativos registrados en sus turnos con respuestas. Los contextos heredados sin registros no se interpretan como cero. Ver `evidencias/preparacion-diseno-usage.json`.

La preparación V1 tenía su propio snapshot separado en el informe original. Para reutilización, los gastos de desarrollo/indexación no se repiten por tarea, pero pueden reaparecer revisión de corpus, cambios, ampliaciones y validación. No se extrapola el porcentaje de este mock a N tareas ni se calcula un punto de equilibrio monetario sin más datos.

## 9. Limitaciones y siguiente validación

- Dos ejecuciones históricas y una nueva, mismo mock conocido: regresión exploratoria sin conclusión causal, estadística ni porcentaje universal.
- Mismo modelo/esfuerzo observado; la modalidad, el formato y la navegación cambian. Semilla, snapshot interno, carga y temperatura no están controlados.
- V2 redujo tokens y llamadas, pero el turno duró 440 s frente a 407 s de V1; no se demostró una mejora de velocidad.
- Menos tokens nativos no se traduce aquí a dinero: no se consultaron precios y caché/razonamiento son subconjuntos, sin doble conteo.
- La fuente AA se recuperó; aún conviene explicitar sus umbrales en el esperado. El validador no prueba apoyo semántico ni detecta toda contradicción entre dudas y casos.
- El primer paquete tuvo una elisión reportada y reparada con replay. Los tokens documentales son proxy de payloads registrados; el contador nativo es la medida acumulada principal.
- La calidad se revisó sin ciego. La consigna ya explicitaba varias excepciones; no es una prueba de descubrimiento espontáneo de todas las reglas ni una validación sobre otras aplicaciones.

La siguiente validación útil sería fijar V2 y ensayarla en varias features nuevas y otro corpus, con criterios previos, evaluadores ciegos cuando sea posible y más de una repetición. También comparar con navegación manual por el índice existente. Este ensayo no ejecutó ninguna prueba sobre OWUI.

## 10. Evidencias y reproducción

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
