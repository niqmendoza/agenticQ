# Comportamiento de la evaluación V2

Evaluación documental independiente en español. El mock se trató como extensión propuesta, sin afirmar existencia. No se ejecutó la aplicación, no se modificaron fuentes, no se navegó Internet, no se crearon subagentes ni se leyeron informes/casos ajenos. Todos los archivos producidos están en la carpeta asignada evaluacion.

## Recuperación y decisiones de navegación

Se leyeron las dos instrucciones operativas asignadas. Toda evidencia del corpus provino exclusivamente de stdout de brain.py V2, usando la base de db/session/log-dir indicada. No se abrieron directamente fuentes, índice SQLite, inventario, snapshot ni código de scripts. Las invocaciones y resultados del navegador están registrados por el propio navegador en lecturas/. El archivo de consultas inicial se pasó como argumento sin imprimirlo.

Se ejecutó un solo pack inicial con las cinco preguntas fijadas y parámetros exactos: seeds 2, related 5, max-docs 20, max-lines 120, max-tokens 14000 y max-chars 50000. La llamada exterior usó max_output_tokens 26000 y exec_command 24000. No se transformó ni recortó stdout.

El paquete recuperó permisos, roles, subida, sistema híbrido, scheduler, URLs firmadas, MinIO, routers, errores y notas de navegación/diseño. El índice quedó incompleto desde línea 121 y la lista pending estaba acotada: pending_total=68 y pending_list_truncated=true. No se interpretó el ranking ni document_complete como garantía de cobertura total. El rango pendiente del índice era principalmente navegación, no un contrato de renovación; no se completó por inercia.

Se ampliaron por show, siempre con max-lines 120/max-tokens 5000/max-chars 20000, las notas relacionadas pertinentes: patrones frontend críticos, JWT y sesiones, cascada, patrones Svelte, i18n, roles semánticos, dark mode, errores frontend, SPA, proveedor de almacenamiento, SSRF, path traversal, Storage Dashboard, Azure AD y ECO Design System. Se usaron rutas devueltas por el paquete o sus enlaces, sin inspeccionar corpus por otros medios.

Se consultaron links de MOC Almacenamiento y MOC Autenticación y Permisos (limit 12, offset 0): ambas listas completas con next_offset=null. Para MOC Diseño y Frontend se completaron las dos páginas, offsets 0 y 12. Se eligieron excepciones y restricciones de las relaciones antes de cerrar: cascada frente a scheduler, estado pending frente a excepciones ACL, frontend de errores y cancelación, factory global frente a paths mixtos. Storage Dashboard aclaró que monitoreo es admin; esa restricción no se extrapoló a renovar File para un user con read. Se descartaron ampliaciones sin incidencia directa como CI/CD, tipografía y resto de índices, registrando el límite en omisiones.

## Fallos y truncamiento observado

La presentación del pack inicial mostró una elisión marcada como aproximadamente 152 tokens dentro de Sistema híbrido de almacenamiento, alrededor de proveedores/fallback. Aunque el navegador marcaba document_complete=true, eso no demostraba que el modelo hubiera recibido todo el texto. Se volvió a pedir show de esa nota, líneas 32–60, con --replay. El stdout de relectura se presentó completo y se usó para los hechos de providers y fallback. No se reconstruyó contenido omitido de memoria ni se usaron fuentes directas para verificar.

No hubo errores de ejecución de brain.py. Algunas solicitudes show pedían hasta 120 y respondieron beyond_eof=true: el propio resultado informa fin de documento; no se citó fuera del total real. No hubo otras elisiones visibles en ampliaciones. Links devuelve relaciones, no cuerpos: esas líneas de enlaces no se usaron como prueba del contenido destino sin show.

## Criterio de elaboración

Se separaron hechos documentados, implementación propuesta, inferencias, preguntas, tensiones de alcance y omisiones. Las fuentes son objetos con rutas originales relativas a OWUI, líneas y sección exactas. Una fuente que contextualiza un requisito propuesto no se usó para atribuirle el contrato nuevo: los límites TTL y el endpoint propuesto se identifican como nuevos en kind/text/oracle.

Los casos son documentales y no representan tests ejecutados. Se parametrizaron estados equivalentes por oráculo: límites TTL, JWT, vías read, estados de UI y locales/temas. Se distinguieron escenarios con consecuencias diferentes, por ejemplo referencia local protegida y enlace S3 previo; cambio de chat y respuesta vieja en el mismo chat; registro inexistente y objeto físico faltante. Cada caso enumera precondiciones, pasos, esperado y origen del oráculo.

Se revisaron personalmente esperados para no presentar como contrato documentado: herencia write→read, chequeo de existencia física por firmar, actualización de last_accessed_at, recuperación local de objetos S3, atomicidad ante revocación/migración/borrado y timeout de la acción. El matiz adicional de 60.0 quedó separado como interpretación abierta de entero estricto, manteniendo 422 inequívoco para fracciones, booleanos, texto y fuera de rango.

Las preguntas Q01–Q09 hacen visibles las decisiones faltantes. Los casos dependientes llevan open_questions y oracle_status=pendiente; no se adjudicó pass/fail definitivo. En especial no se promete que renovar extienda retención ni que revoque enlaces ya emitidos. Los códigos 401/403/404/503/504 adoptan la jerarquía documentada como diseño propuesto de esta acción; su contrato final requiere aprobación de especificación, sin bloquear esta entrega documental.

Se envió al coordinador únicamente el aviso de recuperación completada antes de compartir casos, según la instrucción de entrega. No se intercambiaron resultados con otro evaluador.

## Verificación y congelación

Se ejecutó verify sobre el resultado propio con requirements.json y save=verificacion.json. La primera pasada informó cero referencias inválidas/no entregadas, cero fallos, ningún requisito P1–P7 ni criterio A–G sin casos y cero duplicados exactos. Los avisos correspondieron a oráculos pendientes. Tras revisión semántica se añadió la fuente precisa MinIO para una tensión de alcance y se explicitó la subvariante TTL 60.0/Q09; se repitió el verificador antes de congelar.

La pasada final devolvió 38 casos, 193 citas, cero referencias inválidas/no entregadas, cero fallos, cero duplicados exactos, P1–P7 y A–G cubiertos. Los nueve avisos corresponden a C08, C14, C20, C23, C25, C26, C27, C29 y C38, todos marcados pendientes por decisión abierta.

El verificador valida estructura, rangos, entrega y etiquetas; no prueba apoyo semántico, calidad exhaustiva ni comportamiento de la aplicación. La entrega se congela con SHA256 de resultado.json y comportamiento.md en congelado.json. Después de crear ese archivo no se continúa editando.
