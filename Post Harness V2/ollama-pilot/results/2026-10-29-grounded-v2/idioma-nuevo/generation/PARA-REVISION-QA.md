# Borradores para QA · Idioma inicial e idioma eliminado

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

## C1 · Idioma inicial por defecto

**Precondiciones**

- No especificadas.

**Pasos propuestos**

1. Iniciar una sesión sin establecer preferencia de idioma previa.
2. Verificar que la interfaz se presenta configurada en Castellano Rioplatense (`es-AR`).

**Regla documental para el resultado esperado**

> COELSA.Intelligent tiene configurado **Castellano Rioplatense (`es-AR`)** como idioma por defecto de la interfaz.

**Fuentes**

- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E1
- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E2
- Internacionalización i18n.md · P6578cb1030ea2230d6fc6d33 · E15

## C2 · Idioma en-US eliminado

**Precondiciones**

- No especificadas.

**Pasos propuestos**

1. Acceder a la lista de idiomas disponibles en la configuración del perfil.
2. Confirmar que el identificador `en-US` no figura en la lista de opciones.

**Regla documental para el resultado esperado**

> - `en-US` — Inglés americano (reemplazado por en-GB)

**Fuentes**

- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E9
- Idioma por defecto es-AR.md · P2746c4bc471bfb50fd11c10a · E6
- Internacionalización i18n.md · P6578cb1030ea2230d6fc6d33 · E15

## Preguntas abiertas

- El usuario sugiere comprobar que &#x27;en-US&#x27; ya no está entre los idiomas ofrecidos. La documentación (E6, E9, E15) confirma explícitamente que &#x27;en-US&#x27; fue removido en v1.3.0 y reemplazado por &#x27;en-GB&#x27;. Por lo tanto, la verificación debe consistir en confirmar que &#x27;en-US&#x27; no aparece en la lista de idiomas disponibles y que &#x27;en-GB&#x27; sí está presente.
- El usuario sugiere comprobar el idioma por defecto al abrir una sesión sin preferencia previa. La documentación (E1, E2, E3, E12, E16) establece claramente que el idioma por defecto es &#x27;es-AR&#x27; (Castellano Rioplatense) configurado en el entorno y definido como el estado &#x27;Default&#x27; en los archivos de traducción.

## Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.
