# Modalidad B — navegación con scripts
Carpeta de entrega: /Users/nmendoza/Desktop/Code/QA agentizada/Post Harness/evidencias/scripts
No leer corpus completo, snapshot, inventario, índice SQLite, código de los scripts ni carpetas de otras evaluaciones. Toda evidencia documental debe obtenerse exclusivamente por salida de brain.py con --log-dir. El índice ya está preparado; no reindexar.
Ejecutar PRIMERO las cinco consultas de consultas-evaluacion.json en orden, sin modificar sus textos. Por cada una usar --limit 3 --max-chars 9000 y max_output_tokens=4000. Después elegir autónomamente ampliaciones por query/show/links según evidencia insuficiente, sin límite total obligatorio ni objetivos de ahorro. No continuar desde un resultado truncado sin declararlo: decidir si ampliar y justificar. Una salida acotada no es exhaustiva.
Comando base:
python3 '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness/scripts/brain.py' --db '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness/evidencias/indice.sqlite' --log-dir '/Users/nmendoza/Desktop/Code/QA agentizada/Post Harness/evidencias/scripts/lecturas' query 'texto' --limit 3 --max-chars 9000
Ampliación:
... show 'ruta relativa exacta' --start 1 --end 80 --max-lines 80
... links 'ruta relativa exacta' --limit 20 --offset 0
Salida JSON muestra path, section, start/end, sha256, extracto literal, metadata cruda y enlaces hasta 6 por resultado (más vía links). next_offset y next_line permiten paginar. Los enlaces pueden ser ambiguos o faltar; no asumir que faltante equivale a inexistente. Los metadatos no prueban vigencia. Buscar excepciones, dependencias, dudas y versiones; ampliar si el extracto no contiene evidencia suficiente. No leer directamente fuentes para completar citas.
