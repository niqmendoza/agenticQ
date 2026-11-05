# Inicio rápido con GitHub Copilot

Abrí este repositorio y el proyecto de la aplicación en Copilot. Tené acceso autorizado al segundo cerebro, al código y al entorno de pruebas. Compartí con Copilot `scripts/PROMPT-COPILOT.md` y completá los campos; no incluyas contraseñas ni claves. El proyecto de la aplicación y su comando de pruebas dependen del equipo: no están configurados aquí.

## Opción A · Segundo cerebro como carpeta local

Python 3.10+ en macOS o Linux. En una terminal, desde la raíz de este repositorio, reemplazá las rutas y preguntas por las tuyas. `QA_BRAIN_DIR` apunta a la carpeta **real** de documentos; el directorio de trabajo debe quedar fuera de ella. La salida puede contener documentación interna: protegela y no la subas a Git.

```sh
export QA_BRAIN_DIR="/ruta/absoluta/al/segundo-cerebro"
export QA_WORK_DIR="/ruta/privada/fuera-del-segundo-cerebro"
mkdir -p "$QA_WORK_DIR"
printf '%s\n' '["funcionalidad y reglas relevantes", "restricciones y errores"]' > "$QA_WORK_DIR/preguntas.json"
python3 "Post Harness V2/scripts/brain.py" --db "$QA_WORK_DIR/indice.sqlite" index "$QA_BRAIN_DIR"
python3 "Post Harness V2/scripts/brain.py" --db "$QA_WORK_DIR/indice.sqlite" --session "$QA_WORK_DIR/sesion.json" pack --queries-json "$QA_WORK_DIR/preguntas.json" > "$QA_WORK_DIR/contexto.json"
```

Entregá `contexto.json` a Copilot y pedile que examine `pending`, rangos faltantes y fuentes. Usá una sesión nueva por tarea; `--replay` permite releer lo ya entregado. Ver [documentación completa](../Post%20Harness%20V2/README.md). La sesión registra intervalos entregados y no demuestra que el modelo los haya comprendido.

## Opción B · Segundo cerebro en RAGFlow

Configurá una conexión propia sin secretos: URL y dataset reales según [guía de contexto](../Post%20Harness%20V2/GUIA-CONTEXTO-RAGFLOW.md) y el esquema de `Post Harness V2/ragflow-local/connection.json`. El ID de ejemplo corresponde al ensayo y no identifica tu dataset. Definí `RAGFLOW_API_KEY` por el mecanismo privado del equipo, sin escribirlo en archivos versionados. Si el campo `api_key_env` de tu conexión tiene otro nombre, usá esa variable.

```sh
export QA_CONFIG="/ruta/privada/conexion.json"
export QA_WORK_DIR="/ruta/privada/fuera-del-corpus"
mkdir -p "$QA_WORK_DIR"
python3 "Post Harness V2/scripts/retrieve.py" --config "$QA_CONFIG" --application "NOMBRE_APLICACION" --session "$QA_WORK_DIR/sesion-rag.json" --query "funcionalidad y reglas relevantes" --out "$QA_WORK_DIR/contexto-rag.json"
python3 "Post Harness V2/scripts/verify_context.py" "$QA_WORK_DIR/contexto-rag.json"
```

La ruta de salida debe ser nueva. Revisá estado, omisiones y resultados no devueltos; un contexto válido no asegura cobertura. El bloqueo de sesión usa `fcntl`; Windows no está validado. El arranque de RAGFlow local es opcional y específico del ensayo, no configura automáticamente el segundo cerebro de una aplicación nueva.

## De casos a ejecución

Pedile a Copilot que prepare borradores con fuentes, preguntas abiertas y criterios observables. Tras la revisión de QA, indicá la ruta del proyecto de aplicación, ambiente autorizado, datos de prueba y comando/framework conocidos; Copilot debe inspeccionar el proyecto, implementar pruebas adecuadas y ejecutar el comando real. Si faltan, debe solicitar la información, no adivinar ni afirmar ejecución. Guardá resultados y código de salida, distinguiendo fallas, bloqueos y pruebas no ejecutadas. `draft_cases.py` es una alternativa opcional con Ollama local para generar borradores desde `qa-context/1`; requiere modelo y servicio configurados como explica su [guía](../Post%20Harness%20V2/GUIA-GENERACION-4B.md).
