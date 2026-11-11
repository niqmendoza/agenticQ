# Protocolo V2 — fijado antes de evaluar

Comparación solicitada: iteración 1 lectura completa, iteración 2 scripts V1, iteración 3 scripts V2. Se preservan sin cambios el HTML y toda la carpeta V1. Se reutilizan los dos turnos históricos ya congelados y se agrega un evaluador V2 con fork_turns=none, misma consigna funcional y snapshot OWUI. No es una repetición simultánea aleatorizada: es una regresión exploratoria.

V2 cambia recuperación, formato e instrucciones de navegación. No se usa baseline/resultado.json ni respuestas V1 como entrada del índice o del evaluador. El coordinador conoce omisiones previas (incluida accesibilidad), por eso esta feature sirve como regresión y no como holdout. No se prometerá generalización a otra feature o corpus.

Se implementará paquete multiconsulta, ranking persistido, expansión acotada por enlaces genéricos, fuentes compactas, registro por tarea de intervalos entregados, ampliación sólo de intervalos faltantes, distinción rango/documento completo, verificación de citas y cobertura estructural. No MCP, embeddings, modelo externo ni nuevo harness.

Calibración funcional ajena al mock: routing urlIdx y CSP dev/OpenShift. Pesos y presupuesto se congelan antes de ejecutar V2 sobre el mock; no se ajusta búsqueda según sus casos finales. Las cinco consultas son las mismas del ensayo anterior, agrupadas en pack. Ampliaciones libres y explícitas, sin objetivo obligatorio de ahorro.

Modelo/esfuerzo se heredan sin override y se verifican en turn_context. Usage por respuesta única del primer turno completo; cacheada incluida en entrada, razonamiento incluido en salida. No sumar snapshots acumulativos. Separar preparación, verificación del coordinador y cualquier seguimiento. Registrar payloads presentados y conteo proxy o200k_base aparte. No inferir factura monetaria.

Criterios de calidad A–G previos, mismos que la consigna. No usar cantidad de casos como puntaje. Revisar permisos, TTL, storage, excepciones, efectos, UI, fuentes y duplicados. Las pruebas sólo validan herramientas documentales, no la aplicación real.

La demostración HTML es un esquema visual de los tres flujos, con cifras reales rotuladas; no representa una reproducción exacta de decisiones internas. El Markdown conserva protocolo, implementación, evidencias, límites y comparaciones detalladas.
