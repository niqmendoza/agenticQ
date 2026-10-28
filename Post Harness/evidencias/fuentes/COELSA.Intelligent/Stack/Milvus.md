---
title: "Milvus"
type: stack
tags: [coelsa-intelligent, stack, milvus, vectores, rag]
aliases: [Milvus stack, Base vectorial COELSA]
description: "Usar cuando necesitás configurar Milvus, entender las colecciones del sistema RAG o diagnosticar problemas de embeddings."
estado: vigente
---

# Milvus

## Qué es

COELSA.Intelligent usa **Milvus 2.4+** como base de datos vectorial para el sistema RAG. El esquema implementa [[Milvus multi-tenancy|multi-tenancy]] con 5 colecciones compartidas en lugar de una colección por recurso.

## Versión mínima

Milvus **2.4** — requerido para el soporte de `resource_id` como campo escalar filtrable y mejoras de rendimiento en búsquedas con filtro booleano.

## Configuración

```env
MILVUS_URI=http://localhost:19530
ENABLE_MILVUS_MULTITENANCY_MODE=true
```

## Colecciones

Las [[Cinco colecciones Milvus]] fijas son:
- `_knowledge` — Bases de conocimiento
- `_files` — Archivos subidos
- `_memories` — Memorias de usuarios
- `_web_search` — Resultados de búsqueda web
- `_hash_based` — URLs (YouTube, páginas web)

## Módulo principal

```
backend/server/retrieval/vector/dbs/milvus_multitenancy.py
```

Este módulo implementa `_get_collection_and_resource_id()` que determina a qué colección pertenece un recurso basándose en convenciones de nombre (prefixes).

**Advertencia**: cambiar cómo el frontend genera nombres de colección sin actualizar esta función puede provocar mezcla de datos entre recursos.

## Relacionado

- [[Milvus multi-tenancy]] — La decisión de diseño de las 5 colecciones compartidas
- [[Cinco colecciones Milvus]] — Detalle de cada colección y su uso
- [[Aislamiento por resource_id]] — Cómo se filtra por recurso en las búsquedas
- [[Módulo de retrieval]] — El módulo de Python que orquesta embeddings y búsqueda
- [[MOC - Stack]] — Contexto de Milvus en el stack completo
