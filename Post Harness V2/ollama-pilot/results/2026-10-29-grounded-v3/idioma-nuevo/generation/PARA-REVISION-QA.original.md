# Borradores para QA · Idioma inicial e idioma eliminado

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

## C1 · Verificación del idioma inicial al iniciar sesión sin configuración previa

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
- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E2
- Internacionalización i18n.md · P6578cb1030ea2230d6fc6d33 · E15

## C2 · Verificación de la ausencia de &#x27;en-US&#x27; en la lista de idiomas disponibles

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
- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E9
- Internacionalización i18n.md · P6578cb1030ea2230d6fc6d33 · E15

## Observaciones y preguntas para QA

- El usuario sugiere comprobar que &#x27;en-US&#x27; ya no está entre los idiomas ofrecidos. La documentación (E6, E9, E15) confirma explícitamente que &#x27;en-US&#x27; fue removido en v1.3.0 y reemplazado por &#x27;en-GB&#x27;. Por lo tanto, la verificación debe consistir en confirmar que &#x27;en-US&#x27; no aparece en la lista de idiomas disponibles y que &#x27;en-GB&#x27; sí está presente.
- El usuario sugiere comprobar el idioma por defecto al abrir una sesión sin preferencia previa. La documentación (E1, E2, E3, E12, E16) establece claramente que el idioma por defecto es &#x27;es-AR&#x27; (Castellano Rioplatense) configurado en el entorno y definido como el estado &#x27;Default&#x27; en los archivos de traducción.
- ¿Cómo se presenta visualmente el idioma seleccionado en la interfaz de usuario (bandera, texto o código)?
- ¿Existen otros idiomas corporativos específicos que deban estar presentes además de los mencionados en las reglas?

## Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.
