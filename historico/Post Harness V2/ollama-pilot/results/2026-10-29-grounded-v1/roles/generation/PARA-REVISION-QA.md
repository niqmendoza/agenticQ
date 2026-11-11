# Borradores para QA · Acceso al chat según rol

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

## Preguntas abiertas

- El requisito solicitado implica que un usuario con rol `pending` puede &#x27;intentar usar el chat&#x27; y luego, tras un cambio de rol gestionado por admin, acceder al mismo. Sin embargo, la regla E4 establece explícitamente que el rol `pending` tiene como única capacidad &#x27;ver la pantalla de espera&#x27;, sin poder usar el chat. La transición mencionada en la consigna contradice funcionalidades basadas en reglas documentales si se interpreta literalmente como una prueba de flujos existentes.

## Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.
