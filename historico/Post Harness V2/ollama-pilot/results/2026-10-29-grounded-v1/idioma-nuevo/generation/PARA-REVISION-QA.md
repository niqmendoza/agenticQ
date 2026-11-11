# Borradores para QA · Idioma inicial e idioma eliminado

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

## Preguntas abiertas

- Discrepancia: El documento [[Idioma por defecto es-AR.md]] afirma que el sistema **típicamente** o **está configurado con castellano rioplatense (es-AR)** como idioma por defecto, basándose en `DEFAULT_LOCALE=es-AR`. Sin embargo, no existe una regla explícita que establezca un comportamiento automático de detección del idioma (heuristic logic) ni que garantice que el navegador **siempre** use es-AR como primera opción antes de aplicar las configuraciones del sistema operativo o la página web. Esto impide proponer con certeza absoluta uno de los 10 casos solicitados.
- Ambigüedad: La solicitud implica buscar &#x27;en-US&#x27; no entre los idiomas ofrecidos. Aunque el documento [[Idioma por defecto es-AR.md]] lista explícitamente que fue removido (&#x27;En Inglés americano (reemplazado por en-GB)&#x27;), se solicita verificar su ausencia específica en la interfaz de usuario. Para garantizar la veracidad del caso, se requiere confirmar dónde y cómo se presentan los idiomas listados, ya que el documento no describe exhaustivamente todos los menús ni endpoints donde ocurren las selecciones visuales.

## Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.
