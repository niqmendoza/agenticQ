# Primer lote de borradores · Qwen 4B

**Pendiente de revisión de QA. Ningún caso está aprobado, ejecutado ni publicado.**

Estas consignas son un ensayo documental del segundo cerebro; no representan una funcionalidad nueva aprobada por el equipo. Las notas siguientes son observaciones del asistente, no una revisión independiente de QA.

El JSON de cada entrega conserva el recorte crudo, el hash y el rango de caracteres del fragmento. Los esperados y citas se copian desde el catálogo; la coherencia de los pasos y la selección siguen requiriendo revisión.

---

## Acceso al chat según rol

Dos borradores; el caso negativo usa la prohibición documentada y la transición incluye el cambio por admin.

**Ajustes detectados antes de aprobar**

- Agregar una acción de acceso al chat DESPUÉS del cambio de rol; el segundo caso hoy termina al modificarlo.
- Reemplazar el paso interno “el sistema evalúa” por una observación verificable de la interfaz.
- Revisar las observaciones del modelo: algunas vuelven a pedir detalles técnicos que no impiden un borrador funcional.

### Borrador generado, conservado sin corrección semántica

### Borradores para QA · Acceso al chat según rol

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

#### C1 · Usuario pendiente intenta acceder al chat

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
  - Regla consultada: Rol: pending | Descripción: En espera de aprobación | Capacidades principales: Solo puede ver la pantalla de espera; no puede usar el chat
- Roles de usuario.md · P3cfbc640474ec8bb30233e47 · E5
  - Regla consultada: Un usuario recién logeado por primera vez via Azure AD puede quedar en estado `pending` si la configuración requiere aprobación manual. Un admin debe cambiar el rol a `user` para habilitar el acceso.

#### C2 · Administrador habilita el acceso al chat para usuario pendiente

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
  - Regla consultada: Un usuario recién logeado por primera vez via Azure AD puede quedar en estado `pending` si la configuración requiere aprobación manual. Un admin debe cambiar el rol a `user` para habilitar el acceso.
- Roles de usuario.md · P3cfbc640474ec8bb30233e47 · E4
  - Regla consultada: Rol: pending | Descripción: En espera de aprobación | Capacidades principales: Solo puede ver la pantalla de espera; no puede usar el chat

#### Observaciones y preguntas para QA

- El usuario solicita que el admin cambie el rol de un usuario `pending` a `user` como parte de la transición. El documento E5 confirma que &#x27;Un admin debe cambiar el rol a `user` para habilitar el acceso&#x27;, pero no especifica los pasos técnicos ni el endpoint exacto para realizar este cambio, ni menciona si el cambio es automático o requiere una acción explícita del admin en una interfaz específica. Por lo tanto, no se puede definir el comportamiento de la transición (pasos, endpoints) sin inventar detalles que no están documentados.
- ¿Cuál es la interfaz específica donde el administrador debe realizar el cambio de rol?
- ¿El cambio de rol requiere una confirmación adicional o es inmediato?

#### Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.

---

## Vigencia de un acceso temporal ya emitido

Un borrador; usa la URL después de cambiar permisos y el esperado conserva su validez hasta expirar. No agregó un código HTTP al esperado.

**Ajustes detectados antes de aprobar**

- Confirmar que las precondiciones identifiquen una URL ya emitida y todavía vigente.
- Separar, si corresponde al alcance, otro caso sobre la emisión de nuevas URLs.
- QA debe resolver la discrepancia con la sugerencia utilizada en esta consigna de ensayo.

### Borrador generado, conservado sin corrección semántica

### Borradores para QA · Vigencia de un acceso temporal ya emitido

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

#### C1 · Acceso mediante URL firmada emitida antes del cambio de permisos

**Precondiciones**

- Existe un archivo con una URL de acceso temporal firmada y válida.
- El usuario ha obtenido la URL firmada previamente.

**Pasos propuestos**

1. El administrador modifica los permisos del archivo para restringir el acceso.
2. El usuario intenta acceder al recurso utilizando la URL firmada obtenida antes del cambio de permisos.
3. El sistema responde con éxito al recurso (acceso permitido).

**Regla documental para el resultado esperado**

> - **Control de acceso**: si el [[Control de acceso a recursos|access_control]] del archivo cambia, las URLs viejas siguen siendo válidas hasta su expiración pero no se generan nuevas

**Fuentes**

- URLs firmadas MinIO.md · Ped1b4d66f84df5122f50e633 · E5
  - Regla consultada: - **Control de acceso**: si el [[Control de acceso a recursos|access_control]] del archivo cambia, las URLs viejas siguen siendo válidas hasta su expiración pero no se generan nuevas

#### Observaciones y preguntas para QA

- El usuario sugiere que cambiar los permisos debe invalidar inmediatamente una URL firmada ya emitida. La regla E5 establece explícitamente que &#x27;las URLs viejas siguen siendo válidas hasta su expiración&#x27;. Esto crea una discrepancia: la sugerencia del usuario contradice la documentación oficial sobre la persistencia de la validez de la firma criptográfica una vez generada.
- ¿Es válido para el usuario que la sugerencia de invalidar inmediatamente una URL firmada al cambiar permisos contradiga la regla E5 que establece que las URLs viejas permanecen válidas hasta su expiración?

#### Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.

---

## Tiempo de inactividad sin confirmar

No genera caso ni inventa quince minutos; conserva la pregunta sobre el comportamiento no documentado.

**Ajustes detectados antes de aprobar**

- Pedir la regla funcional de inactividad y su fuente antes de diseñar ese caso.

### Borrador generado, conservado sin corrección semántica

### Borradores para QA · Tiempo de inactividad sin confirmar

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

#### Observaciones y preguntas para QA

- La solicitud pide confirmar el comportamiento de cierre de sesión de un usuario con rol `pending` tras 15 minutos de inactividad. En los documentos proporcionados (Roles de usuario.md, Storage Dashboard.md), se define que el rol `pending` permite solo ver la pantalla de espera y no usar el chat, pero no existe ninguna regla que especifique un tiempo de inactividad, ni el comportamiento de cierre automático de la sesión en ese estado.

#### Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.

---

## Idioma inicial e idioma eliminado

Dos borradores; reconoce es-AR y la exclusión de en-US con respaldo documental.

**Ajustes detectados antes de aprobar**

- El esperado principal del caso de en-US es una frase introductoria demasiado general. Especificarlo con las reglas concretas de apoyo antes de automatizar.
- Confirmar los datos y la forma real de observar el idioma inicial y la lista de opciones.

### Borrador generado, conservado sin corrección semántica

### Borradores para QA · Idioma inicial e idioma eliminado

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

#### C1 · Verificación del idioma inicial al iniciar sesión sin configuración previa

**Precondiciones**

- El usuario no ha establecido preferencias de idioma en la configuración del sistema.
- Se ha iniciado una nueva sesión de usuario.

**Pasos propuestos**

1. Observar el idioma predeterminado que se muestra como selección activa al abrir la interfaz.
2. Verificar si el idioma configurado corresponde a &#x27;Castellano Rioplatense&#x27; (es-AR).

**Regla documental para el resultado esperado**

> COELSA.Intelligent tiene configurado **Castellano Rioplatense (`es-AR`)** como idioma por defecto de la interfaz.

**Fuentes**

- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E1
  - Regla consultada: COELSA.Intelligent tiene configurado **Castellano Rioplatense (`es-AR`)** como idioma por defecto de la interfaz.
- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E2
  - Regla consultada: ```env DEFAULT_LOCALE=es-AR ```
- Internacionalización i18n.md · P6578cb1030ea2230d6fc6d33 · E15
  - Regla consultada: Removidos en v1.3.0: `es-ES`, `pt-PT`, `en-US`. Ver [[Idioma por defecto es-AR]].

#### C2 · Verificación de la ausencia de &#x27;en-US&#x27; en la lista de idiomas disponibles

**Precondiciones**

- El sistema está configurado en la versión v1.3.0 o superior.
- El usuario accede a la lista de selección de idiomas.

**Pasos propuestos**

1. Revisar la lista completa de idiomas ofrecidos para su selección.
2. Confirmar que el código &#x27;en-US&#x27; (Inglés americano) no figure entre las opciones disponibles.
3. Confirmar que el código &#x27;en-GB&#x27; (Inglés británico) sí esté presente en la lista.

**Regla documental para el resultado esperado**

> Los siguientes idiomas fueron removidos porque no aplican al contexto corporativo de COELSA:

**Fuentes**

- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E6
  - Regla consultada: Los siguientes idiomas fueron removidos porque no aplican al contexto corporativo de COELSA:
- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E9
  - Regla consultada: - `en-US` — Inglés americano (reemplazado por en-GB)
- Internacionalización i18n.md · P6578cb1030ea2230d6fc6d33 · E15
  - Regla consultada: Removidos en v1.3.0: `es-ES`, `pt-PT`, `en-US`. Ver [[Idioma por defecto es-AR]].

#### Observaciones y preguntas para QA

- El usuario sugiere comprobar que &#x27;en-US&#x27; ya no está entre los idiomas ofrecidos. La documentación (E6, E9, E15) confirma explícitamente que &#x27;en-US&#x27; fue removido en v1.3.0 y reemplazado por &#x27;en-GB&#x27;. Por lo tanto, la verificación debe consistir en confirmar que &#x27;en-US&#x27; no aparece en la lista de idiomas disponibles y que &#x27;en-GB&#x27; sí está presente.
- El usuario sugiere comprobar el idioma por defecto al abrir una sesión sin preferencia previa. La documentación (E1, E2, E3, E12, E16) establece claramente que el idioma por defecto es &#x27;es-AR&#x27; (Castellano Rioplatense) configurado en el entorno y definido como el estado &#x27;Default&#x27; en los archivos de traducción.
- ¿Cómo se presenta visualmente el idioma seleccionado en la interfaz de usuario (bandera, texto o código)?
- ¿Existen otros idiomas corporativos específicos que deban estar presentes además de los mencionados en las reglas?

#### Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.

