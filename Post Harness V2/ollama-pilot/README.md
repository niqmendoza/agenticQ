# Siguiente ensayo · generación local con Saluki

Preparación del 29/10/2026. **Saluki no se instaló ni se ejecutó en esta Mac.** Los archivos de esta carpeta son un perfil y una plantilla para el próximo ensayo; no constituyen una integración terminada ni casos aprobados.

## Decisión

Podemos probar la generación con Ollama sin una licencia de GitHub Copilot. Copilot tiene [acceso gratuito con límites](https://docs.github.com/en/copilot/how-tos/manage-your-account/get-started-with-a-copilot-plan); para esta ruta el modelo se invoca directamente mediante la API local de Ollama.

Flujo previsto: requisito de ensayo → contexto recuperado de RAGFlow → modelo local → borradores con citas → revisión de QA. Desarrollo recibe información sobre los casos; no se agrega una autorización obligatoria de desarrollo. La comparación con Azure y la publicación de casos aún no están conectadas.

## Qué se verificó

La Mac consultada es una **MacBook Air M4, arm64, con 16 GB de memoria unificada**. El servidor Ollama responde con versión **0.35.1** y el ejecutable de terminal con **0.31.1**. Se observó un desfase entre ambos. No se cambió ninguno.

El candidato es **Underdog Saluki 27B 1.0**, una cuantización de Qwen3.8-27B. El archivo de texto publicado ocupa **7.898.369.152 bytes**. El autor documenta importación GGUF a Ollama y una prueba en Apple Silicon con **Ollama 0.40.4**. Esto respalda la posibilidad de probarlo, no certifica esta Mac ni demuestra una versión mínima obligatoria. [Ficha del publicador](https://huggingface.co/ConwayResearch/Underdog-Saluki-27B-1.0).

Ollama admite [aceleración Metal en Apple](https://docs.ollama.com/gpu). El tamaño del archivo no incluye todo el costo de ejecución: contexto, caché y buffers consumen memoria adicional; [aumentar el contexto aumenta la memoria requerida](https://docs.ollama.com/context-length).

En esta medición, los cinco servicios de RAGFlow sumaron aproximadamente **4,7 GiB** de memoria de contenedores. Esa suma no incluye todo Docker Desktop. El sistema ya usaba aproximadamente **2,7 GiB de swap** y quedaban alrededor de **14 GiB de disco**. Son observaciones de este momento, no requisitos generales del modelo.

**Evaluación:** el hardware es candidato para una prueba de texto con contexto corto. No se confirmó que RAGFlow y Saluki funcionen simultáneamente con buen rendimiento. Tampoco se midieron velocidad, memoria máxima, calidad en español o utilidad para QA.

## Archivos preparados

- `preflight.json`: hardware sin números de serie, versiones observadas, identidad y revisión del candidato.
- `Modelfile.saluki`: perfil inicial de 4.096 tokens de contexto y hasta 1.024 de salida. No incluye pesos.
- `generation-request.template.json`: solicitud a `/api/chat` con salida estructurada, citas y preguntas abiertas. Reemplazar todos los marcadores antes de usarla; es una plantilla experimental de ensayo, no el estándar final de casos.

El contexto incluye entrada y salida: para este primer perfil usar una consulta pequeña, reservar espacio para la respuesta y comprobar el conteo del modelo. No pegar un paquete de 6.000 tokens en una ventana de 4.096 ni asumir que `o200k_base` coincide con el tokenizer de Qwen. El esquema JSON controla forma; no garantiza que las citas sustenten el resultado esperado. [API de chat](https://docs.ollama.com/api/chat), [salida estructurada](https://docs.ollama.com/capabilities/structured-outputs).

## Próxima ejecución

1. Dar margen al disco para pesos, importación y swap; no se borraron archivos ni modelos para obtenerlo. La importación puede requerir espacio adicional a la descarga.
2. Alinear servidor y CLI con una versión actual de Ollama. La [release estable consultada](https://github.com/ollama/ollama/releases/tag/v0.40.13) es 0.40.13. La actualización y su efecto sobre los modelos existentes todavía no se probaron.
3. Descargar el GGUF exacto identificado en `preflight.json` e importarlo con el perfil preparado. No se presupone que `ollama pull saluki` sea un tag oficial disponible.
4. Preparar una tarea acotada y recuperar su contexto mientras RAGFlow está disponible. Medir primero el margen de memoria antes de mantener ambos servicios generando a la vez. Si no alcanza, evaluar separar RAGFlow y Ollama entre equipos.
5. Probar carga y respuesta breve; después generar hasta tres borradores. Registrar conteos nativos, tiempos, memoria, swap y salida literal, sin publicar en Azure.
6. Verificar formato, IDs y citas; QA revisa respaldo, suficiencia y correcciones. La validación humana sigue pendiente hasta completar este paso.

No se ejecutaron descargas, actualizaciones, importaciones ni solicitudes generativas como parte de esta preparación.

## Ensayo posterior con modelos pequeños

Se instaló Qwen3.5 de 0.8B y se lo comparó con el 4B ya disponible. Ver [resultados del ensayo](RESULTADO-MODELOS-PEQUENOS.md). La ejecución de esos modelos no completa la evaluación de Saluki ni la aprobación de QA.
