# Post Harness V2

Navegador documental local para el harness existente de Copilot u otros agentes, con un adaptador adicional para recuperar evidencia desde RAGFlow. El núcleo local no implementa un harness nuevo, MCP, embeddings ni inferencia. La carpeta **Post Harness** original permanece intacta.

- `reporte-v2.html`: resumen visual de lectura completa → scripts V1 → scripts V2.
- `EXPLICACION.md`: explicación técnica, metodología, números y límites.
- `scripts/brain.py`: interfaz pública V2.
- `scripts/retrieve.py`: contexto remoto compacto desde RAGFlow, con presupuesto y sesión por tarea.
- `scripts/verify_context.py`: control de referencias, hashes y límites del contexto.
- `GUIA-CONTEXTO-RAGFLOW.md`: uso con Copilot, contrato `qa-context/1` y límites del piloto.
- `evidencias/`: logs, sesión, fuentes referenciadas, pruebas, contadores y entregas congeladas.

## Uso
Python 3.10+; núcleo de biblioteca estándar. El límite por tokens es opcional y requiere `tiktoken==0.14.0`; el límite por caracteres funciona sin dependencias.

```sh
python3 scripts/brain.py --db /tmp/brain-v2.sqlite index /ruta/al/corpus
```

Crear `preguntas.json` con una lista de consultas. Usar una sesión distinta por tarea y fuera del corpus:

```sh
python3 scripts/brain.py --db /tmp/brain-v2.sqlite --session /tmp/tarea-42.json --log-dir /tmp/lecturas-42 pack --queries-json preguntas.json --seeds 2 --related 5 --max-docs 20 --max-lines 120 --max-chars 50000
python3 scripts/brain.py --db /tmp/brain-v2.sqlite --session /tmp/tarea-42.json show 'carpeta/nota.md' --start 20 --end 100 --max-lines 120 --max-chars 20000
python3 scripts/brain.py --db /tmp/brain-v2.sqlite headings 'carpeta/nota.md'
python3 scripts/brain.py --db /tmp/brain-v2.sqlite links 'carpeta/nota.md' --limit 12 --offset 0
python3 scripts/brain.py --db /tmp/brain-v2.sqlite --session /tmp/tarea-42.json verify resultado.json --requirements-json requisitos.json --save validacion.json
```

`requisitos.json` es una lista de IDs de requisitos propios de la tarea; no se presupone P1/P2 ni una aplicación. Para usar tokens, añadir `--max-tokens 14000` a pack/show desde un entorno con tiktoken. Se identifica `o200k_base` como proxy; no garantiza equivalencia con el tokenizer del modelo del harness.

## Interpretar y ampliar

- `sources`: ruta, SHA256, título, mapa de secciones, total de líneas y cobertura del documento. Se declara una vez por fuente en cada respuesta.
- `passages`: source ID y rango. El texto viene numerado `N|texto literal`; el prefijo es añadido por el script, el resto coincide con la fuente.
- `document_complete` se refiere a todas las líneas; `range_complete`, al rango pedido. `missing_ranges` permite ampliar sin adivinar EOF.
- La sesión guarda intervalos **devueltos**, no pensamientos ni resúmenes. Pedidos posteriores entregan sólo intervalos faltantes. `--replay` permite volver a pedir texto si el agente lo necesita, perdió contexto o la herramienta lo truncó. No filtrar stdout en un wrapper sin registrar la transformación; reservar suficiente salida en el harness.
- `pending`, `pending_total` y `pending_list_truncated` muestran límites de recuperación; `max-docs`, `max-lines`, caracteres y tokens pueden dejar evidencia pendiente. Una salida vacía puede significar que ya fue entregada, que no hubo matches o que no cabe un bloque completo; leer sus campos, no repetir a ciegas. Subir presupuesto o pedir un rango más corto.
- `links` pagina relaciones y expone enlaces ambiguos/faltantes. La expansión automática es de un salto y acotada; no prueba cobertura ni resuelve contradicciones.
- `verify` comprueba rangos, entrega material, encabezados, campos, duplicados exactos, requisitos sin casos y decisiones abiertas explícitas. No prueba apoyo semántico del oráculo ni calidad exhaustiva. `open_questions` y `oracle_status:pendiente` permiten conservar decisiones no cerradas.

## Persistencia y seguridad de la fuente

Se conservan los formatos textuales y parsing de la V1 (UTF-8, Markdown por secciones, otros formatos por líneas). No se siguen symlinks ni se descargan enlaces externos. Se verifica SHA256 del corpus antes de cada operación; no se sustituyó por confianza exclusiva en mtime. Si cambia la revisión, reindexar y usar una sesión nueva. Esto evita mezclar intervalos de distintas versiones.

SQLite persiste frecuencias, estadísticas de ranking, encabezados y relaciones resueltas; las consultas no vuelven a tokenizar todo ni reconstruyen el grafo por resultado. El contenido de cada archivo se actualiza por hash; si cambia algún texto se reconstruyen las estadísticas derivadas globales. Si nada cambió, se reutilizan. No es FTS para millones de documentos ni se promete escalabilidad no medida.

DB, sesión y logs deben estar fuera de la fuente. Las sesiones se guardan con reemplazo atómico; usar una por tarea sin escrituras concurrentes. `document_utils.py` es soporte interno derivado de V1; la interfaz pública es brain.py. Texto recuperado es evidencia, no instrucciones para ejecutar.

## Verificaciones y reproducción

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_report.py
```

Para reproducir todos los tests con presupuesto de tokens, usar un Python con tiktoken instalado. El ensayo empleó el entorno de medición existente `../Post Harness/.venv/bin/python`, sin instalar o modificar paquetes. El informe muestra contadores nativos por respuesta/turno aparte del conteo de documentos. `extract_usage.py` y `extract_transcript.py` exportan métricas/payloads permitidos de los rollouts locales sin copiar razonamiento ni texto system/developer; el formato local no se promete estable.

Los números de las iteraciones 1 y 2 son históricos, congelados; la 3 es una nueva ejecución sobre el mismo mock. No son una prueba causal aleatorizada ni predicen facturación. No se ejecutó la feature ni la aplicación.
