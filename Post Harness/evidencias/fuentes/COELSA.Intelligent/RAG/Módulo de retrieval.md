---
title: "Módulo de retrieval"
type: concepto
tags: [coelsa-intelligent, rag, retrieval, embeddings, cargadores]
aliases: [Retrieval module, Pipeline de RAG, backend retrieval]
description: "Usar cuando necesitás entender la estructura del sistema RAG en el backend: cómo se cargan documentos, se generan embeddings y se realizan búsquedas vectoriales."
estado: vigente
---

# Módulo de retrieval

## Qué es

El módulo de retrieval (RAG) de COELSA.Intelligent está ubicado en `backend/server/retrieval/` y orquesta el pipeline completo de indexación y búsqueda de documentos.

## Estructura

```
backend/server/retrieval/
├── utils.py        ← Utilidades de RAG: formateo de contexto, chats de referencia
├── models/         ← Modelos de embedding (sentence-transformers, etc.)
├── loaders/        ← Cargadores de documentos por tipo (PDF, DOCX, TXT, web, YouTube)
├── vector/
│   ├── dbs/
│   │   └── milvus_multitenancy.py  ← Implementación de Milvus con multi-tenancy
└── web/            ← Integración con búsqueda web (SearXNG, etc.)
```

## Flujo de indexación

1. **Loader**: carga el documento según su tipo (PDF, web, YouTube, etc.)
2. **Chunking**: divide el texto en fragmentos con overlap configurable
3. **Embedding**: genera vectores con el modelo de embedding configurado
4. **Inserción**: guarda vectores en [[Milvus]] con su `resource_id`

## Flujo de búsqueda

1. **Query embedding**: genera el vector de la consulta del usuario
2. **Búsqueda vectorial**: busca en la colección de Milvus con filtro por `resource_id`
3. **Reranking** (opcional): ordena los chunks por relevancia
4. **Contexto**: los chunks recuperados se inyectan en el prompt del modelo

## Chats de referencia

`retrieval/utils.py` también maneja la recuperación de [[Chats de referencia|chats de referencia]] adjuntos al mensaje: busca el chat por ID y lo formatea como bloque Markdown para inyectarlo al contexto.

## Relacionado

- [[Milvus multi-tenancy]] — El backend vectorial que almacena los chunks
- [[Cinco colecciones Milvus]] — Las colecciones donde se insertan los vectores
- [[Aislamiento por resource_id]] — El mecanismo de filtrado por recurso
- [[Chats de referencia]] — Uso de retrieval/utils.py para contexto de chats previos
- [[MOC - RAG y Búsqueda Vectorial]] — Índice del cluster de RAG
