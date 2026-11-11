import hashlib, json, pathlib, sys, tempfile, time

sys.path.insert(0, sys.argv[1])
import brain

corpus = pathlib.Path(sys.argv[2])
queries = [
    "permisos de usuario roles chat",
    "acceso lectura archivos seguridad",
    "modelo tokens ventana limite",
    "contexto documentos búsqueda y embeddings",
    "RAGFlow conocimiento recuperación",
    "funciones herramientas integración",
    "frontend UI navegación accesibilidad",
    "grupos roles administrador permisos",
    "almacenamiento archivos MinIO carga",
    "errores tiempo límites reintentos",
] * 2
with tempfile.TemporaryDirectory() as d:
    t = time.perf_counter()
    brain.index(corpus, pathlib.Path(d) / "index.sqlite")
    index_elapsed = time.perf_counter() - t
    c, cfg, settings = brain.checked(pathlib.Path(d) / "index.sqlite")
    times = []
    for _ in range(5):
        t = time.perf_counter()
        result = (
            brain.rank_queries(c, settings, queries)
            if hasattr(brain, "rank_queries")
            else [brain.ranking(c, settings, q) for q in queries]
        )
        times.append(time.perf_counter() - t)
    c.close()
    print(
        json.dumps(
            {
                "index_seconds": round(index_elapsed, 4),
                "search_median_seconds": round(sorted(times)[len(times) // 2], 4),
                "result_sha256": hashlib.sha256(
                    json.dumps(result, sort_keys=True).encode()
                ).hexdigest(),
            }
        )
    )
