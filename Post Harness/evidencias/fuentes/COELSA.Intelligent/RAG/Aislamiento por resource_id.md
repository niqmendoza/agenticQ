---
title: "Aislamiento por resource_id"
type: concepto
tags: [coelsa-intelligent, rag, milvus, resource-id, aislamiento]
aliases: [resource_id Milvus, Filtro por recurso, Vector isolation]
description: "Usar cuando necesitás entender cómo se garantiza que las búsquedas vectoriales devuelven solo datos del recurso correcto en el esquema multi-tenancy de Milvus."
estado: vigente
---

# Aislamiento por resource_id

## Qué es

En el esquema de [[Milvus multi-tenancy|multi-tenancy de Milvus]], el aislamiento entre recursos se logra mediante un campo escalar llamado `resource_id` que se almacena junto a cada vector.

## Cómo funciona

**Al insertar** un vector (chunk de texto):
```python
# Se incluye resource_id en los metadatos del punto
{
    "vector": [0.1, 0.2, ...],
    "resource_id": "knowledge-abc123",
    "content": "texto del chunk",
    "metadata": {...}
}
```

**Al buscar**:
```python
# Se aplica un filtro booleano sobre resource_id
search_results = collection.search(
    data=[query_embedding],
    filter=f'resource_id == "{resource_id}"',
    ...
)
```

Esto garantiza que los resultados de búsqueda pertenecen exclusivamente al recurso solicitado.

## Por qué es seguro

Milvus ejecuta el filtro booleano en el nivel de cada segmento, antes de devolver resultados. No es posible que un chunk de un `resource_id` diferente aparezca en los resultados de una búsqueda filtrada por otro `resource_id`, siempre que el campo esté indexado correctamente.

## Cómo se genera el resource_id

El `resource_id` se deriva del identificador del recurso (ID de la Knowledge base, ID del archivo, etc.) mediante una convención de nombres que la función `_get_collection_and_resource_id()` en `milvus_multitenancy.py` implementa.

## Relacionado

- [[Milvus multi-tenancy]] — El diseño del que este mecanismo es parte
- [[Cinco colecciones Milvus]] — Las colecciones donde se usa resource_id
- [[Módulo de retrieval]] — El módulo que aplica los filtros en las búsquedas
- [[MOC - RAG y Búsqueda Vectorial]] — Índice del cluster de RAG
