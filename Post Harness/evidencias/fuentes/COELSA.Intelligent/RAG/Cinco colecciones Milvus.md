---
title: "Cinco colecciones Milvus"
type: referencia
tags: [coelsa-intelligent, rag, milvus, colecciones]
aliases: [Colecciones Milvus, Milvus collections COELSA]
description: "Usar cuando necesitás saber a qué colección de Milvus va un tipo específico de contenido (archivos, knowledge, memorias, web, URLs)."
estado: vigente
---

# Cinco colecciones Milvus

## Qué es

En el esquema de [[Milvus multi-tenancy]], hay exactamente **5 colecciones fijas** en [[Milvus]]. Cada tipo de contenido tiene su colección designada.

## Las colecciones

| Colección | Contenido | Cuándo se usa |
|-----------|-----------|---------------|
| `_knowledge` | Chunks de bases de conocimiento | Al embedir una Knowledge base |
| `_files` | Chunks de archivos subidos por usuarios | Al embedir un archivo de chat |
| `_memories` | Memorias de usuario | Al guardar o recuperar memorias personalizadas |
| `_web_search` | Resultados de búsqueda web embebidos | Al indexar resultados de búsqueda para RAG |
| `_hash_based` | URLs: páginas web, videos YouTube | Al indexar contenido de URLs |

## Cómo se determina la colección

La función `_get_collection_and_resource_id()` en `milvus_multitenancy.py` analiza el nombre o el tipo del recurso para determinar a qué colección pertenece. Usa **convenciones de prefijos** en los nombres generados por el frontend.

**Regla crítica**: El frontend y esta función deben estar en sincronía. Si el frontend cambia cómo nombra los recursos, esta función debe actualizarse.

## Aislamiento dentro de cada colección

Dentro de cada colección, los registros de diferentes usuarios/recursos están separados por el campo `resource_id`. Ver [[Aislamiento por resource_id]].

## Relacionado

- [[Milvus multi-tenancy]] — El diseño de las 5 colecciones compartidas
- [[Aislamiento por resource_id]] — El mecanismo de aislamiento por recurso
- [[Módulo de retrieval]] — El módulo que escribe y lee de estas colecciones
- [[MOC - RAG y Búsqueda Vectorial]] — Índice del cluster de RAG
