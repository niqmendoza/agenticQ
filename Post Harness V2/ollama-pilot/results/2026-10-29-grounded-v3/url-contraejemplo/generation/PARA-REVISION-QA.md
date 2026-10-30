# Borradores para QA · Vigencia de un acceso temporal ya emitido

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

## C1 · Acceso mediante URL firmada emitida antes del cambio de permisos

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

## Observaciones y preguntas para QA

- El usuario sugiere que cambiar los permisos debe invalidar inmediatamente una URL firmada ya emitida. La regla E5 establece explícitamente que &#x27;las URLs viejas siguen siendo válidas hasta su expiración&#x27;. Esto crea una discrepancia: la sugerencia del usuario contradice la documentación oficial sobre la persistencia de la validez de la firma criptográfica una vez generada.
- ¿Es válido para el usuario que la sugerencia de invalidar inmediatamente una URL firmada al cambiar permisos contradiga la regla E5 que establece que las URLs viejas permanecen válidas hasta su expiración?

## Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.
