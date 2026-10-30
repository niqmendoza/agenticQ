# Borradores para QA · Acceso al chat según rol

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

## Preguntas abiertas

- El usuario solicita que el admin cambie el rol de un usuario `pending` a `user` como parte de la transición. El documento E5 confirma que &#x27;Un admin debe cambiar el rol a `user` para habilitar el acceso&#x27;, pero no especifica los pasos técnicos ni el endpoint exacto para realizar este cambio, ni menciona si el cambio es automático o requiere una acción explícita del admin en una interfaz específica. Por lo tanto, no se puede definir el comportamiento de la transición (pasos, endpoints) sin inventar detalles que no están documentados.

## Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.
