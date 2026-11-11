# Primera comprobación · RAGFlow local

Completada el 28 de octubre de 2026.

- RAGFlow `v0.27.3` ejecutándose en Docker Desktop, con su imagen AMD64 sobre esta Mac ARM.
- Cinco servicios con estado saludable: RAGFlow, Elasticsearch, MySQL, almacenamiento compatible MinIO y Valkey.
- Interfaz y API accesibles sólo desde esta máquina: [abrir RAGFlow](http://127.0.0.1:8088/).
- Los **80 Markdown** del snapshot del segundo cerebro coinciden con los hashes del ensayo anterior.
- Los **80 documentos** fueron cargados y terminaron en estado `DONE`, con **143 fragmentos** indexados.
- Embeddings generados con el Ollama local y `nomic-embed-text:latest`; no se configuró un modelo generativo ni un proveedor externo.
- La consulta `archivo renovar lectura permisos access_control propietario admin grupos usuario pending`, reutilizada del ensayo, devolvió **5 fragmentos** con fuentes identificadas. Entre ellas: Roles de usuario, Flujo de subida de archivos y Control de acceso a recursos.
- El cliente HTTP y la regresión existente aprobaron **22 tests**. La carga y consulta anteriores se comprobaron además contra la instancia real.

La respuesta completa de la consulta queda en `state/consulta-ensayo.local.json`. La configuración pública de conexión está en `connection.json`; las credenciales se conservan aparte en `state/credentials.local.json`.

Esto valida arranque, autenticación, carga, indexación y recuperación por API. El ahorro de tokens en Copilot, la calidad de cobertura y el formato de salida se evaluarán en una etapa posterior. El núcleo medido de `brain.py` no fue reemplazado.
