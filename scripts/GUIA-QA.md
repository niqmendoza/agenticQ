# Guía de inicio para QA

1. Abrí este repositorio en un entorno con Copilot habilitado. Abrí [PROMPT-COPILOT.md](PROMPT-COPILOT.md), copiá el bloque y pegalo en el chat de Copilot.
2. Contestá las preguntas que haga. Si no sabés dónde está la documentación, el proyecto o el ambiente de prueba, decíselo: Copilot debe indicarte qué falta y no inventarlo. No compartas contraseñas en el chat.
3. Revisá con Copilot los casos y las dudas. Primero comprobará si la documentación respalda cada caso; después, si puede implementarlo en la aplicación. Tu revisión es necesaria antes de incorporarlos o ejecutarlos.
4. Al terminar, pedile el enlace a `registro-pruebas.csv`. Podés abrirlo en Excel: muestra qué se quería probar, qué se ejecutó, el resultado individual y su evidencia. «Sin resultado individual» significa que no hay evidencia suficiente para ese caso; no significa aprobado ni fallido.
5. Para una nueva release, volvé a pegar el prompt e indicá si existe una funcionalidad nueva. Se recuperan los casos de regresión ya revisados; se agregan casos nuevos sólo para esa funcionalidad. Si cambiaron reglas, corresponde revisarlos.

El flujo depende de que Copilot tenga acceso a los archivos, al segundo cerebro, al proyecto y a un ambiente autorizado. Las pruebas, los resultados y la importación a Azure no se dan por realizados hasta contar con evidencia. La [guía técnica](FLUJO-PORTABLE.md) describe los pasos y el [paquete de evidencia](VALIDACION-Y-EVIDENCIA.md) cómo conservarlos de manera privada.
