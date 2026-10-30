# Borradores para QA · Vigencia de un acceso temporal ya emitido

**Estado: pendiente de revisión de QA. No ejecutar ni publicar automáticamente.**

El resultado esperado copia una regla documental seleccionada. La relación entre esa regla y los pasos todavía necesita revisión semántica.

## Preguntas abiertas

- El usuario sugiere que cambiar los permisos debe invalidar inmediatamente una URL firmada ya emitida. La regla E5 establece explícitamente que &#x27;las URLs viejas siguen siendo válidas hasta su expiración&#x27;. Esto crea una discrepancia: la sugerencia del usuario contradice la documentación oficial sobre la persistencia de la validez de la firma criptográfica una vez generada.
- La sugerencia de validar inmediatamente una URL firmada tras cambiar los permisos del archivo contradice la regla E5, que establece explícitamente que las URLs viejas permanecen válidas hasta su expiración y no se invalidan por cambios en el control de acceso.

## Alcance de la revisión

QA revisa pertinencia, vigencia, coherencia de los pasos, cobertura y duplicados. Desarrollo permanece informado, sin aprobación obligatoria de los casos. El JSON conserva los hashes y los rangos de caracteres dentro del fragmento para comprobar las fuentes.
