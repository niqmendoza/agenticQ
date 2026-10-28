# Comportamiento de la evaluación — modalidad scripts

## Alcance y decisiones

Evaluación independiente íntegramente documental en español. No se ejecutó la aplicación, no se ejecutaron tests de aplicación, no se modificaron fuentes y no se navegó Internet. No creé subagentes ni leí entregables de otras evaluaciones. La renovación se trata como extensión propuesta. Los hechos describen lo escrito en las notas, sin certificar implementación ni vigencia desplegada.

Toda evidencia del corpus se recuperó exclusivamente por salidas de brain.py con --db del índice preparado y --log-dir de esta carpeta. No leí código de brain.py, corpus, snapshot ni SQLite directamente y no reindexé. Las lecturas iniciales de consignas y configuración se registraron además en lecturas/000-instrucciones-y-consultas.json. Los logs nativos de brain.py conservan invocaciones, resultados, revisión, hashes y límites.

Ejecuté primero y en orden las cinco consultas exactas de consultas-evaluacion.json con --limit 3 --max-chars 9000 y max_output_tokens=4000. Cada una devolvió dos resultados por presupuesto, next_offset=2 y truncated=true. Lo declaré antes de ampliar. No consideré exhaustivos esos resultados ni interpreté missing_terms como ausencia funcional.

## Ampliaciones y justificación

- Permisos: show completo de Control de acceso a recursos, Roles de usuario y Grupos y permisos para separar None, {}, read/write, propietario/admin y pending. El extracto inicial no contenía toda la tabla de modos. La query posterior access_control write read herencia permisos no documentó herencia write→read; mantuve la duda sin convertir la ausencia léxica de herencia en prueba.
- Storage: show de URLs firmadas MinIO, Sistema híbrido, Flujo de subida y Agregar proveedor. Permitió comprobar objeto específico, 3600 configurable, URLs previas, rama local y separación get/upload/delete. Leí el final del proveedor (81–94) al advertir total_lines=94, aunque el show 1–80 devolvió truncated=false y next_line=null: esos campos no significan documento completo.
- Efectos laterales: show de Scheduler de limpieza y Borrado en cascada para last_accessed_at, umbral de más de 30 días, cada 24 horas desde arranque, huérfanos y chat_id. No asumí que renovar renueve retención.
- Backend: show de Agregar router REST y Sistema de errores centralizado. Query JWT get_current_user expiración autenticación y show de JWT para identidad; el resultado Headers de usuario aclaró que no se leen headers para autenticar router. No convertí el pseudocódigo JWT en garantía de actualización de roles por sí mismo.
- Frontend: show de Patrones frontend críticos y Patrones de componentes Svelte, incluido remanente línea 81; show de i18n, errores, roles semánticos y dark mode. Query SPA ssr false SvelteKit y show de SPA respaldaron la continuidad del modo cliente. La guarda de contexto/generación para esta nueva acción es inferencia de diseño, no un endpoint existente.
- Seguridad: show de Path Traversal como dependencia. P1 evita aceptar path/URL del cliente; la sanitización de upload no se usa como sustituto del control de File por ID.

Las consultas autónomas conservaron --limit 3 con --max-chars 16000 o 14000. También fueron truncadas por cantidad de resultados y se trataron como búsquedas de orientación. Sus rutas útiles se ampliaron por show; no paginé todo el ranking porque eso no asegura cobertura y las lagunas restantes requieren decisiones de producto o contratos específicos. Los enlaces a las notas relevantes fueron suficientes para elegir show; no ejecuté links. No asumí que un enlace faltante equivaliera a ausencia.

La quinta consulta obligatoria devolvió incidentalmente una sección de COELSA.Intelligent/OKF-INDEX.md con rutas de Diseño Frontend y metadatos/enlaces generales. No abrí el índice ni inventario por show ni recorrí el corpus; usé únicamente las rutas específicas devueltas para llegar a las notas relevantes. Esta exposición incidental queda registrada como limitación respecto de la prohibición de leer inventarios.

## Fallos, truncamientos y límites

No hubo comandos fallidos ni truncamiento adicional del terminal observado. Los recortes de query están declarados arriba y guardados en los logs. show puede devolver beyond_eof=true si el pedido superaba el final; no es fallo. La relación truncated=false en show no demuestra que no haya líneas después del end solicitado: revisé total_lines y completé dos remanentes. relations_truncated=true en queries significa que los enlaces visibles son solo una parte; no hice afirmaciones de exhaustividad de enlaces.

Los metadatos crudos estado: vigente no verifican vigencia. Las referencias a v1.3.0 se limitaron a idiomas/defaults documentados, sin asumir que sean la versión desplegada. No abrí un changelog completo ni fuentes externas. La evidencia recuperada basta para una propuesta trazable con dudas visibles, no para certificar el comportamiento del software.

## Relecturas y diferencia entre salida nativa y presentada

La verificación de citas repitió show 1–80 para cada una de las 21 rutas distintas citadas en el borrador. El motivo fue comprobar líneas y encabezados exactos, no ampliar el ranking ni buscar ahorrar lecturas. Esta repetición es parte real de la recuperación y debe contarse. Las llamadas previas de ampliación por show presentaron stdout JSON completo, sin resumirlo ni recortarlo en el wrapper del shell. Las consultas iniciales respetaron sus límites y no sufrieron recorte adicional por max_output_tokens observado.

En esa segunda pasada de verificación, el wrapper subprocess.run(capture_output=True) recibió cada JSON completo de brain.py, que también quedó en su log nativo; json.loads procesó text para imprimir solamente path y una lista de líneas que comienzan con #, eliminando de la salida presentada el cuerpo, metadatos y demás campos. Por eso el stdout efectivamente mostrado al evaluador fue una transformación más breve que los *.result.json nativos de esas 21 llamadas. lecturas/revision-citas.json conserva la invocación descriptiva, el borrador propio leído y el resultado transformado por ruta. No hubo un paginado implícito ni un truncamiento de terminal: la selección de encabezados fue explícita en el wrapper.

El detector startswith('#') también enumeró comentarios dentro de fences de código como si fueran posibles encabezados. No se usaron esos comentarios como secciones documentales. Las correcciones separaron los encabezados Markdown reales ya observados en los shows completos; corrigieron el comienzo de Agregar una traducción (47), el de AbortController (27) y ampliaron la referencia de extracción de message hasta 51. Esta transformación no reemplaza el registro nativo de lectura ni oculta que se volvió a solicitar contenido ya recuperado.

La paginación real fue solo la ampliación explícita de los remanentes del proveedor (81–94) y Svelte (81), debido a total_lines mayor que 80 aun con truncated=false/next_line=null. No se paginaron los rankings OR ni los enlaces. La consulta obligatoria que devolvió OKF-INDEX y la lectura de sus extractos quedaron registradas sin una apertura adicional del índice.

## Tratamiento del oráculo y deduplicación

Los casos son escenarios documentales propuestos y no resultados ejecutados. Cada caso identifica P o hechos F; kind=inferencia señala recomendaciones cuyo resultado binario depende de decisión. Las fuentes documentales no se inventan para políticas P: sources=[] cuando el único respaldo es la consigna propuesta. Parametricé tipos y fronteras TTL, roles/permisos, errores y locales/temas. Separé carreras de borrado, migración y ACL porque cambian el estado y el oráculo. No impuse last_accessed_at ni herencia write/read como comportamiento validado.

Las preguntas cubren política de último acceso, TTL local/null/60.0, existencia física, punto de consistencia, relación chat/File, contrato de errores y providers adicionales. Los conflictos distinguen tensión textual real, diferencias de alcance y peligros de inferencia. El aviso de recuperación al coordinador se emitió sin compartir casos, como exige la consigna; fue el único contacto de coordinación.

## Entrega

resultado.json contiene hechos, implementación propuesta, casos, preguntas, conflictos y omisiones. Esta nota describe navegación y límites. Se verificaron encabezados y líneas de las citas con nuevas salidas brain.py show, separando referencias que cruzaban secciones. Se verificó la estructura JSON y las claves sin probar la aplicación; el registro de esa verificación se guarda en lecturas. congelado.json fija SHA256 de resultado.json y comportamiento.md. No se editarán tras el congelado. No calculé tokens.
