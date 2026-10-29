# Pruebas de recuperación · RAGFlow local

29 de octubre de 2026.

**Resultado:** la API y la persistencia funcionan; la recuperación básica necesita ampliaciones para entregar contexto suficiente.

Se conservaron 80 documentos y 143 fragmentos tras reiniciar Docker. Pasaron 27 tests automatizados, incluidos cinco controles nuevos para interpretar el evaluador.

| Modalidad | Señales documentales | Tokens de salida del cliente (proxy) |
|---|---:|---:|
| Scripts locales V2 · paquete inicial | 8/14 | 13.796 |
| RAGFlow · 5 fragmentos por consulta | 8/14 | 21.753 |
| RAGFlow · 10 fragmentos por consulta | 9/14 | 41.621 |
| RAGFlow · 5 + ampliaciones dirigidas | 14/14 | 35.867 |

Subir de 5 a 10 fragmentos incrementó la salida un **91.3%** y sólo sumó una señal. Las seis ampliaciones dirigidas completaron el checklist con 11 llamadas en total.

En la salida del cliente de cinco fragmentos, el texto documental suma 9.959 tokens proxy frente a 21.753 del JSON completo. La diferencia incluye metadatos, campos derivados y envolturas; no equivale a un ahorro ya implementado.

## Reglas que faltaron en la consulta básica

- Restricción del usuario pendiente: `Roles de usuario.md`.
- Validación de sesión en endpoints protegidos: `JWT y sesiones.md`.
- Omitir detalles internos en producción: `Sistema de errores centralizado.md`.
- Colores semánticos en ambos temas: `Roles semánticos de color.md`.
- Cancelar solicitudes anteriores del chat: `Patrones frontend críticos.md`.
- Umbrales de contraste AA: `ECO Design System.md`.

## Consultas ajenas al dominio

| Umbral | Consultas ajenas sin resultados | Señales de la aplicación |
|---|---:|---:|
| 0.2 | 0/4 | 8/14 |
| 0.28 | 1/4 | 8/14 |
| 0.3 | 2/4 | 7/14 |

La similitud no garantiza que exista una respuesta. No se cambió el umbral de conexión: la calibración no mostró una solución suficiente.

## Controles técnicos

- API key inválida: rechazada con HTTP 401.
- Dataset inexistente: error explícito, sin evidencia.
- Servicio sin escuchar: error explícito, sin confundirlo con una búsqueda vacía.
- Fragmentos devueltos: todos pertenecen al dataset y a los documentos cargados.
- Repetición: mismos conjuntos de fragmentos en las cinco consultas, tanto con 5 como con 10 resultados.

## Siguiente ajuste recomendado

Preparar una capa de recuperación que amplíe sólo donde falta evidencia, reúna fuentes y evite repetir contenido. El formato de salida sigue pendiente; estas pruebas no lo fijan. El diseño de esa capa debe distinguir el documento encontrado de la regla efectivamente recuperada.

También conviene evaluar el modelo de embeddings antes de reindexar: el adaptador Ollama inspeccionado envía documentos y consultas sin prefijos de tarea. La [documentación de Nomic](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) prescribe prefijos distintos para búsqueda y documentos. Es un posible factor, no una causa aislada en este ensayo. La implementación revisada pertenece a [RAGFlow v0.27.3](https://github.com/infiniflow/ragflow/blob/v0.27.3/rag/llm/embedding_model.py).

## Límites de interpretación

- Son 14 señales documentales del mismo mock conocido. No son 14 pruebas ejecutadas sobre la aplicación ni una medición exhaustiva de cobertura.
- Las consultas dirigidas estaban prefijadas a partir de lo que sabíamos que faltaba. Esta prueba no demuestra que Copilot o un agente las descubran solos.
- El paquete inicial local y las cinco consultas de RAGFlow usan políticas distintas de selección y límites. Recuperan la misma cantidad de señales, pero no exactamente las mismas.
- Los tokens son un proxy o200k_base del contenido serializado. No son el consumo nativo de Copilot ni una factura; faltan generación, historial, reintentos y caché.
- Se repitieron dos veces las cinco consultas por perfil. Eso comprueba estabilidad en este entorno, sin demostrar rendimiento o robustez general.
- RAGFlow transforma tablas Markdown en HTML al indexar. No se deben inventar rangos de líneas originales para esos fragmentos.

## Reproducir

Desde `Post Harness V2`:

```sh
"../Post Harness/.venv/bin/python" ragflow-local/evaluate_retrieval.py --out ragflow-local/pruebas/NUEVA-EJECUCION
"../Post Harness/.venv/bin/python" ragflow-local/calibrate_retrieval.py --out ragflow-local/pruebas/NUEVA-CALIBRACION
"../Post Harness/.venv/bin/python" -m unittest discover -s tests -v
```

Cada ejecución requiere una carpeta nueva. Conserva protocolo, solicitudes sin encabezados de autenticación, respuestas nativas, salida del cliente, paquete local y resumen. No sobrescribe las evidencias históricas.

Evidencias iniciales: `pruebas/2026-10-29-inicial`. Calibración: `pruebas/2026-10-29-calibracion`.
