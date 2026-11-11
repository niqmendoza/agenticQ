---
title: "MOC — RAG y Búsqueda Vectorial"
type: moc
tags: [coelsa-intelligent, rag, milvus, vectores, moc]
aliases: [MOC RAG, Búsqueda Vectorial COELSA, RAG COELSA]
description: "Usar cuando trabajás con embeddings, retrieval, colecciones Milvus o chats de referencia en COELSA.Intelligent."
estado: vigente
---

# MOC — RAG y Búsqueda Vectorial

El sistema RAG usa [[Milvus]] con un esquema de [[Milvus multi-tenancy|multi-tenancy]] de 5 colecciones compartidas. El aislamiento entre recursos se logra con filtros por [[Aislamiento por resource_id|resource_id]].

## Notas de este cluster

- [[Milvus multi-tenancy]] — Esquema de 5 colecciones compartidas vs una por recurso; decisión de diseño y trade-offs
- [[Cinco colecciones Milvus]] — Las cinco colecciones fijas: `_knowledge`, `_files`, `_memories`, `_web_search`, `_hash_based`
- [[Aislamiento por resource_id]] — Cómo el campo `resource_id` filtra chunks en búsquedas para garantizar aislamiento
- [[Módulo de retrieval]] — Estructura de `backend/server/retrieval/`; cargadores, embeddings, función de búsqueda
- [[Chats de referencia]] — Adjuntar conversaciones previas como contexto en el input de mensajes

## MOCs vecinos

- [[MOC - Stack]] — Milvus como componente del stack; dependencia de versión 2.4+
- [[MOC - Modelos IA y Routing]] — Cómo los modelos consumen el contexto generado por RAG
- [[MOC - Almacenamiento]] — Los archivos que se embedden también viven en MinIO
- [[MOC - Decisiones]] — Decisión de multi-tenancy con justificación de overhead de escalado
