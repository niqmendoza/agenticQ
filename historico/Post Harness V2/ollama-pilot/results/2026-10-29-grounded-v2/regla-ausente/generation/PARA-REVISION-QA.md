# Borradores para QA · Tiempo de inactividad sin confirmar

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

## Preguntas abiertas

- La solicitud pide confirmar el comportamiento de cierre de sesión de un usuario con rol `pending` tras 15 minutos de inactividad. En los documentos proporcionados (Roles de usuario.md, Storage Dashboard.md), se define que el rol `pending` permite solo ver la pantalla de espera y no usar el chat, pero no existe ninguna regla que especifique un tiempo de inactividad, ni el comportamiento de cierre automático de la sesión en ese estado.

## Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.
