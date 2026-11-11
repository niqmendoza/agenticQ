# Borradores para QA · Acceso al chat según rol

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

## C1 · Usuario pendiente intenta acceder al chat

**Precondiciones**

- El usuario está autenticado y su rol actual es `pending`.
- El sistema está activo.

**Pasos propuestos**

1. El usuario intenta iniciar una conversación o enviar un mensaje en el chat.
2. El sistema evalúa las capacidades del rol `pending`.

**Regla documental para el resultado esperado**

> Rol: pending | Descripción: En espera de aprobación | Capacidades principales: Solo puede ver la pantalla de espera; no puede usar el chat

**Fuentes**

- Roles de usuario.md · P3cfbc640474ec8bb30233e47 · E4
- Roles de usuario.md · P3cfbc640474ec8bb30233e47 · E5

## C2 · Administrador habilita el acceso al chat para usuario pendiente

**Precondiciones**

- Existe un usuario con rol `pending`.
- El administrador tiene credenciales válidas y permisos de gestión.

**Pasos propuestos**

1. El administrador accede a la interfaz de gestión de usuarios.
2. El administrador localiza al usuario `pending` y selecciona la opción para modificar su rol.
3. El administrador cambia el rol del usuario de `pending` a `user`.

**Regla documental para el resultado esperado**

> Un usuario recién logeado por primera vez via Azure AD puede quedar en estado `pending` si la configuración requiere aprobación manual. Un admin debe cambiar el rol a `user` para habilitar el acceso.

**Fuentes**

- Roles de usuario.md · P3cfbc640474ec8bb30233e47 · E5
- Roles de usuario.md · P3cfbc640474ec8bb30233e47 · E4

## Observaciones y preguntas para QA

- El usuario solicita que el admin cambie el rol de un usuario `pending` a `user` como parte de la transición. El documento E5 confirma que &#x27;Un admin debe cambiar el rol a `user` para habilitar el acceso&#x27;, pero no especifica los pasos técnicos ni el endpoint exacto para realizar este cambio, ni menciona si el cambio es automático o requiere una acción explícita del admin en una interfaz específica. Por lo tanto, no se puede definir el comportamiento de la transición (pasos, endpoints) sin inventar detalles que no están documentados.
- ¿Cuál es la interfaz específica donde el administrador debe realizar el cambio de rol?
- ¿El cambio de rol requiere una confirmación adicional o es inmediato?

## Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.
