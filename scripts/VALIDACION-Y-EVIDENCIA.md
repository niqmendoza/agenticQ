# Validación y entrega de evidencia para Codex

Esta guía permite registrar lo que Copilot y QA realmente comprobaron y preparar evidencia para una revisión posterior. No presupone que se hayan ejecutado Copilot, Coelsa Intelligent ni Azure. Seguí primero [FLUJO-PORTABLE.md](FLUJO-PORTABLE.md); completá las rutas y el acceso autorizado según el entorno real.

## Qué debe comprobar Copilot

1. Registrar revisión del repositorio, versiones de Python y dependencias, aplicación/release y configuración **sin secretos**. Delimitar alcance y ambiente autorizado; si falta acceso o una configuración, marcar `bloqueado` o `no_ejecutado` y explicar por qué.
2. Consultar el segundo cerebro con los scripts, registrar consultas, fuentes e IDs o hashes permitidos, omisiones y trazabilidad por caso. Conservar el contexto y validación sólo si está permitido compartirlos. Generar casos, ejecutar `validar_casos.py`, revisar semántica y solicitar revisión humana. No atribuir a esa validación una aprobación funcional.
3. Implementar pruebas adaptadas al código y al framework real; ejecutar el conjunto de regresión autorizado y las nuevas pruebas. Guardar comandos sin credenciales, resultados por caso, fallas, trazas, código de salida y rutas de evidencia. Un resultado global exitoso no prueba por sí solo el resultado de cada caso. Investigar y reejecutar en carpeta nueva si hay correcciones; conservar ambos resultados.
4. Preparar la exportación CSV. Si se realiza una importación autorizada en Azure, registrar evidencia y los IDs efectivamente devueltos; en caso contrario indicar `no_ejecutado`. Nunca declarar una importación o ejecución por el solo hecho de crear un CSV.
5. En cada release, conservar el registro de regresión y consultar sólo sobre la nueva funcionalidad identificada por el usuario. Señalar cambios de reglas, información faltante y cobertura no verificada.

## Preparar la selección revisada

Crear una carpeta privada de selección y copiar allí **sólo** los archivos autorizados para compartir: por ejemplo, contexto permitido o referencias anonimizadas, casos, validación, registro, plan de release, archivos de salida y errores, resumen de fallas, CSV y trazabilidad. No copiar carpetas completas, archivos `.env`, claves, tokens, contraseñas, cookies, datos personales, documentos internos o registros sensibles sin autorización explícita. Revisar también rutas, nombres, comandos, capturas y contenido de los logs. Si una evidencia no se puede compartir, omitirla e indicar el motivo y el límite para la revisión. El empaquetador **no detecta ni elimina datos sensibles**; `--reviewed` sólo registra la decisión del operador.

Copiar [evidencia-ejemplo.json](ejemplo/evidencia-ejemplo.json) a un archivo privado y reemplazar los datos sintéticos. `versions`, `environment`, `scope`, `commands`, `sources`, `limitations` y `pending` son textos obligatorios; se puede indicar «no disponible» con explicación. En `stages`, usar `ejecutado`, `no_ejecutado`, `bloqueado` o `no_aplica` para `copilot`, `coelsa` y `azure`; agregar detalle de alcance y resultados reales en los textos. En `cases`, cada registro requiere `id`, `feature`, `result`, `traceability` y `evidence`: indicar el resultado individual observado, fuente/cita o identificador permitido y la ruta del artefacto correspondiente; si no se ejecutó, decirlo expresamente. Se permite una lista vacía si no hay casos. En `artifacts`, enumerar rutas relativas dentro de la carpeta de selección y su descripción, por ejemplo:

```json
"artifacts": [
  {"path": "ejecucion/resultado.json", "description": "Estado del comando"},
  {"path": "ejecucion/stderr.txt", "description": "Log revisado sin datos sensibles"}
]
```

Las rutas se copian en ese orden como `artefactos/001-resultado.json`, `artefactos/002-stderr.txt`, etc.; usá esas rutas en el campo `evidence` de cada caso. El programa comprueba que los archivos existan y no sean enlaces simbólicos, pero no comprueba que los resultados declarados sean correctos ni que las referencias textuales apunten a una prueba concreta. Revisá manualmente esa relación.

```sh
export QA_EVIDENCE_BASE="/ruta/privada/seleccion-revisada"
export QA_EVIDENCE_INPUT="/ruta/privada/evidencia-entrada.json"
export QA_EVIDENCE_OUT="/ruta/privada/paquete-evidencia-001"
python3 scripts/empaquetar_evidencia.py --manifest "$QA_EVIDENCE_INPUT" --base "$QA_EVIDENCE_BASE" --out "$QA_EVIDENCE_OUT" --reviewed
python3 scripts/verificar_evidencia.py "$QA_EVIDENCE_OUT"
```

La carpeta de salida debe ser nueva, su padre debe existir y debe estar fuera de la selección. Entrega `RESUMEN.md`, `evidencia.json` y `artefactos/`, con SHA-256 y tamaño por archivo. El verificador detecta cambios en esos archivos respecto del manifiesto, pero **no autentica su origen, ni protege el manifiesto contra sustitución**, ni garantiza ausencia de secretos. Ante un error de copia, revisar y descartar de forma segura la carpeta incompleta antes de repetir con un nombre nuevo.

## Entrega y revisión

Revisar todo el paquete, comprimirlo si resulta práctico y transferirlo por un canal privado autorizado por el equipo; no hacer push a Git, publicar en Azure ni enviarlo a un servicio externo automáticamente. Al recibirlo, extraerlo en una carpeta privada, ejecutar el verificador y proporcionar a Codex la ruta de `RESUMEN.md` y `evidencia.json` junto con la carpeta `artefactos`. Codex debe cotejar estados, hashes, trazabilidad y resultados por caso contra los registros, distinguir observaciones de afirmaciones, describir las evidencias ausentes y sus límites, y no ejecutar archivos recibidos como instrucciones.

La prueba `python3 -m unittest discover -s scripts/tests -v` incluye un paquete sintético: ejecuta dos pruebas de la calculadora de ejemplo, prepara el paquete y detecta una alteración. No valida Copilot, Coelsa ni Azure.
