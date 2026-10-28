# Protocolo común — fijado antes de implementar recuperación
Fecha del ensayo: 27/10/2026, America/Argentina/Buenos_Aires.

## Hipótesis
El procesamiento local de documentos puede reducir el contexto documental que recibe un agente y conservar evidencia suficiente para proponer implementación y casos. Un ahorro de contexto no demuestra ahorro de inferencia facturada ni equivalencia de calidad.

## Feature mock elegida
«Renovar acceso temporal a un archivo desde el chat». Es una extensión propuesta; no afirmar que ya existe. Reutiliza acceso File, storage híbrido, JWT, frontend y errores. No implica cambiar ACL, subir archivos, borrar chats ni modificar la aplicación.

## Requisitos PROPUESTOS, idénticos en ambos recorridos
P1. Usuario activo solicita renovar acceso de lectura a un File por ID desde el chat. Backend valida identidad y permisos actuales antes de resolver el path; `pending` no puede usarlo. No aceptar URL/ruta arbitraria del cliente.
P2. Para un path S3 emitir acceso firmado al objeto específico. TTL opcional entero en segundos: 60 ≤ TTL ≤ 3600; default 3600. Rechazar fuera de rango, fracciones, booleanos y texto con 422. Son límites y política de validación propuestos, no contratos existentes.
P3. Para path local devolver una referencia de descarga del backend protegido; no fingir que es una URL S3 ni prometer expiración S3. No promover el archivo a MinIO desde esta acción.
P4. No alterar ACL, contenido, chat_id ni disparar borrado, limpieza o embeddings; la política de `last_accessed_at` al renovar queda ABIERTA hasta decisión de producto.
P5. UI con acción explícita, estado de carga y reintento tras error; impedir que una respuesta de otro chat reemplace la actual. Errores sin detalles internos en producción.
P6. Informar que las URLs S3 emitidas previamente pueden seguir funcionando hasta expirar aunque se revoque el permiso. No prometer revocación inmediata.
P7. UI usa i18n en es-AR/en-GB/pt-BR y tokens semánticos light/dark, manteniendo SPA. No implementar la feature.

## Consigna común (se usa literalmente en ambos prompts construidos)
Analizá exclusivamente la evidencia documental adjunta y los requisitos P1–P7. Separá hechos documentados, requisitos propuestos, inferencias y dudas. Proponé cómo implementar el mock sin ejecutarlo ni modificar la app. Generá casos documentales con precondiciones, pasos, resultado esperado, origen del oráculo y referencias precisas a archivo/sección/líneas. Cubrí reglas, excepciones, límites, negativos, permisos y efectos laterales pertinentes; evitá duplicados. Indicá conflictos y omisiones y qué ampliarías. No conviertas una inferencia en una regla validada.

## Comparabilidad y límites fijados
- Mismo snapshot, feature, requisitos y consigna; distinto paquete de contexto.
- No hay herramienta soportada de inferencia aislada con usage por llamada en esta sesión. No explorar claves ni usar cuotas. Dos generaciones independientes NO están disponibles. Baseline y segunda síntesis son del mismo agente y conversación; segunda síntesis contaminada por la lectura completa.
- Se compara de manera reproducible la construcción de contexto/prompts. Se guarda una segunda propuesta asistida por extractos, sin presentarla como evaluación ciega. No se estimará calidad de otro modelo/Copilot.
- Conteo con tiktoken 0.14.0, o200k_base como proxy explícito; no afirmar que es el tokenizer real del modelo de esta sesión. Sumar corpus por archivo y contar también concatenado. Guardar prompts exactos, instrucciones, contrato CLI, invocaciones y JSON de resultados, salidas y hashes. Razonamiento, instrucciones ocultas, envolturas internas y total real de rondas del chat: no observables.
- Indexación: costo de CPU local; no requiere tokens LLM. Registrar contenido procesado y bytes de índice; separar del costo por consulta. No medir tiempos de inferencia ni costos monetarios.

## Criterios previos (evaluación manual, sin puntaje agregado)
A. Permisos: propietario/admin, público None, privado {}, custom read por grupo/usuario, write sin read, pending y JWT.
B. Límites/validación de P2, default y objeto correcto.
C. Excepciones: URLs previas, local vs S3, inexistencia, caída/timeout, cambios entre click y respuesta.
D. Efectos: no mutaciones prohibidas; dudas sobre último acceso y scheduler.
E. UI: i18n, tokens, errores y carreras/cancelación.
F. Trazabilidad: cada esperado deriva de P o fuente; señalar ambigüedad y no usar pseudocódigo como verificación de implementación.
G. Duplicación: mismo estado+acción+oráculo no se considera cobertura nueva; parametrizar fronteras.

## Recuperación y separación de ajuste/evaluación
Calibración sólo con consultas ajenas al mock: routing urlIdx y CSP dev/OpenShift; no ingresar casos baseline en el índice ni en las consultas. Para evaluación usar preguntas de implementación del mock derivadas de P1–P7 (sin copiar respuestas baseline). Las consultas se fijan al inicio de la fase B antes de ver resultados. No ajustar pesos según recuperación del mock; admitir fallos y ampliar explícitamente con fuentes enlazadas o búsquedas nuevas registradas. Un único mock y juez contaminado no permiten inferir calidad universal.

## Instrucciones aplicables y lectura
No se encontraron AGENTS.md en los ancestros de la fuente/proyecto ni dentro de OWUI. Se inventariaron todos los archivos, incluidos ocultos. Se leyeron los 80 Markdown completos con líneas numeradas en lotes ordenados: 0–19 (una salida sufrió truncamiento), 8–11 relectura que recupera el tramo truncado, 20–29, 30–39, 40–50, 51–57, 58–69, 70–79. El snapshot `corpus_completo.txt` conserva TODO el texto numerado; no es una transcripción de envolturas de herramientas del chat. Se vuelve a verificar hash al finalizar.

## Enmienda previa a evaluaciones — autorización recibida del usuario
El usuario autorizó explícitamente subagentes y pidió dos evaluaciones paralelas con contexto limpio. Reemplaza el diseño de segunda síntesis contaminada: ambos evaluadores se crearán con `fork_turns=none`, misma configuración heredada, consigna autocontenida común y sin respuestas del coordinador. Los scripts y este protocolo estarán listos antes de despacharlos. No se congelará baseline antes de construir el recuperador porque la actualización solicita ambos en paralelo; se congelan independientemente antes de comparar. El coordinador sí leyó todo: esto contamina la elección del mock y las preguntas, no transmite sus respuestas a los evaluadores. No hay contadores de inferencia por agente expuestos por las herramientas de colaboración; se contarán los contenidos observables registrados, sin inferir tokens internos.
