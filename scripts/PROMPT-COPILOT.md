# Prompt para iniciar QA guiado

Copiá el bloque y pegalo en Copilot con este repositorio abierto. No hace falta completar campos antes de empezar.

```text
Ayudame a probar una aplicación. Soy analista de QA y no necesito ver comandos salvo que te los pida. Guiame en español sencillo, con preguntas breves y sólo cuando necesites una respuesta para continuar. No me pidas contraseñas ni secretos.

Primero revisá scripts/GUIA-QA.md, scripts/FLUJO-PORTABLE.md y scripts/VALIDACION-Y-EVIDENCIA.md. Identificá qué información y accesos ya están disponibles. Preguntame únicamente lo que falte para identificar la aplicación, la funcionalidad o release, dónde está su documentación (segundo cerebro), el proyecto y un ambiente de pruebas autorizado. Si algo no está disponible, explicá qué queda bloqueado y avanzá con lo demás; no inventes información ni accedas a producción por suposición.

Usá los scripts para buscar documentación específica y proponer casos con fuentes y dudas. Hacé dos revisiones separadas: (1) comprobá citas con validar_casos.py y revisá si las fuentes realmente respaldan los resultados; (2) inspeccioná la aplicación, su framework y ambiente reales para evaluar si cada caso es viable y cómo implementarlo. Explicame lo que encontraste y pedí mi revisión de reglas, casos y supuestos antes de incorporarlos a la regresión o ejecutarlos. La coincidencia literal no demuestra corrección ni cobertura.

Implementá y ejecutá las pruebas viables en el ambiente autorizado. Conservá los resultados, logs y trazas y analizá los fallos; no afirmes que una prueba se ejecutó o aprobó sin evidencia individual. Si el ejecutor produce JUnit, identificá cada prueba mediante un mapa revisado, procesá resultados_junit.py y conservá el XML; si no, dejá sin resultado individual lo que no puedas respaldar. Generá con exportar.py un CSV para Excel que muestre funcionalidad, prueba prevista, qué se ejecutó, resultado y evidencia por caso. Compartí el enlace al CSV y explicá brevemente las pruebas no ejecutadas o bloqueadas. Si faltan datos para vincular un resultado, decilo.

Conservá los casos revisados y sus pruebas como regresión. En cada release preguntame si hay funcionalidad nueva y cuál es, ejecutá la regresión existente y consultá sólo por la nueva funcionalidad para agregar sus casos revisados, sin regenerar todos. Si cambiaron reglas o falta documentación, señalá los casos afectados para revisión; no supongas que siguen vigentes. Prepará exportación de Azure sólo si tengo sus datos de configuración; no importes ni publiques automáticamente.

Prepará evidencia privada según VALIDACION-Y-EVIDENCIA.md; no subas secretos, datos personales, documentación interna ni logs sensibles. Indicá qué está respaldado, qué falta y dónde quedaron el CSV y la evidencia. No afirmes haber usado Copilot, ejecutado pruebas o importado casos sin que realmente haya ocurrido.
```
