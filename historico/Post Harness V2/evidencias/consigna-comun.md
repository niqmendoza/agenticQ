# Evaluación documental independiente
Trabajá íntegramente en español. No crear subagentes ni contactar otros chats/agentes/personas. No leer entregables del otro evaluador ni resultados de calibración, reporte o análisis del coordinador. No navegar Internet ni ejecutar la aplicación ni modificar fuentes. Usar exclusivamente la modalidad de acceso documental que se te asigna.

## Feature mock: renovar acceso temporal a un archivo desde el chat
Es una extensión propuesta; no afirmar que existe.
P1. Usuario activo solicita renovar acceso de lectura a un File por ID desde el chat. Backend valida identidad y permisos actuales antes de resolver el path; pending no puede usarlo. No aceptar URL/ruta arbitraria del cliente.
P2. Para path S3 emitir acceso firmado al objeto específico. TTL opcional entero en segundos: 60 ≤ TTL ≤ 3600; default 3600. Rechazar fuera de rango, fracciones, booleanos y texto con 422. Son límites y política de validación propuestos, no contratos existentes.
P3. Para path local devolver referencia de descarga del backend protegido; no fingir URL S3 ni prometer expiración S3. No promover el archivo a MinIO desde esta acción.
P4. No alterar ACL, contenido, chat_id ni disparar borrado, limpieza o embeddings; política de last_accessed_at al renovar ABIERTA hasta decisión de producto.
P5. UI con acción explícita, carga y reintento; impedir que una respuesta de otro chat reemplace la actual. Errores sin detalles internos en producción.
P6. Informar que URLs S3 emitidas previamente pueden seguir funcionando hasta expirar aunque se revoque el permiso. No prometer revocación inmediata.
P7. UI usa i18n es-AR/en-GB/pt-BR y tokens semánticos light/dark, manteniendo SPA.

## Consigna
Analizá exclusivamente la evidencia documental adjunta y los requisitos P1–P7. Separá hechos documentados, requisitos propuestos, inferencias y dudas. Proponé cómo implementar el mock sin ejecutarlo ni modificar la app. Generá casos documentales con precondiciones, pasos, resultado esperado, origen del oráculo y referencias precisas a archivo/sección/líneas. Cubrí reglas, excepciones, límites, negativos, permisos y efectos laterales pertinentes; evitá duplicados. Indicá conflictos y omisiones y qué ampliarías. No conviertas una inferencia en una regla validada.

## Criterios
A: propietario/admin, None, {}, read grupo/usuario, write sin read, pending, JWT.
B: default y fronteras/validación TTL, objeto correcto.
C: URLs previas, local vs S3, inexistencia, caída/timeout, carreras.
D: efectos laterales y dudas sobre último acceso/scheduler.
E: UI i18n/tokens/errores/cancelación.
F: trazabilidad por fuente o P; ambigüedades visibles.
G: evitar casos con idéntico estado, acción y oráculo; parametrizar fronteras.

## Entrega
Guardar SOLO en tu carpeta asignada:
- `resultado.json`: objeto con `facts`, `implementation`, `cases`, `questions`, `conflicts`, `omissions`. Cada elemento de facts/implementation lleva `id`, `text`, `kind` (documentado/propuesto/inferencia) y `sources`. Cada caso lleva `id`, `title`, `criteria` (lista A..G), `preconditions`, `steps`, `expected`, `oracle` (P1..P7 y/o hecho documental), `kind` y `sources`. `sources` siempre lista de objetos {path: ruta relativa exacta a OWUI, start: línea inicial, end: final, section: texto del encabezado}. Dudas/conflictos/omisiones pueden ser texto o usar la misma estructura. No inventar fuentes para políticas propuestas; distinguirlo en kind/oracle.
- `comportamiento.md`: decisiones de navegación, ampliaciones, dudas y cualquier fallo/truncamiento de herramientas observado. No calcular tokens tú: el coordinador cuenta archivos exactos. No afirmar tests de aplicación ejecutados.
- `congelado.json`: SHA256 de resultado.json y comportamiento.md. Cerrá con breve estado y rutas; no seguir editando tras congelar.
Las invocaciones y resultados de TODAS las lecturas/consultas deben quedar registrados con las herramientas locales asignadas. Emití al coordinador un aviso cuando hayas completado la recuperación, sin compartir todavía tus casos.
