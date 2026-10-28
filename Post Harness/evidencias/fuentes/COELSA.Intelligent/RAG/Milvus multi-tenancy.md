---
title: "Milvus multi-tenancy"
type: decision
tags: [coelsa-intelligent, rag, milvus, multi-tenancy, arquitectura]
aliases: [Multi-tenancy Milvus, 5 colecciones Milvus, Milvus shared collections]
description: "Usar cuando necesitás entender por qué Milvus usa 5 colecciones compartidas en lugar de una por recurso, y qué trade-offs implica esta decisión."
estado: vigente
---

# Milvus multi-tenancy

## Qué es

La implementación de [[Milvus]] en COELSA.Intelligent usa un esquema de **multi-tenancy con 5 colecciones fijas compartidas** para todos los usuarios y recursos, en lugar del esquema del upstream que crea una colección por cada archivo o recurso.

## Motivación del cambio

El esquema del upstream (una colección por recurso) genera **overhead significativo al escalar**:
- Milvus tiene un límite práctico de colecciones que puede gestionar eficientemente
- Con muchos usuarios subiendo archivos, el número de colecciones crece sin límite
- El tiempo de carga de colecciones al iniciar Milvus escala con la cantidad de colecciones

Con 5 colecciones fijas, el overhead de gestión de colecciones es constante independientemente de cuántos usuarios y archivos tenga el sistema.

## Aislamiento garantizado

El aislamiento entre recursos se logra mediante el campo `resource_id` en cada vector. Ver [[Aislamiento por resource_id]].

## Advertencia crítica

El mapeo de colecciones depende de convenciones de prefijos de nombres (cómo el frontend genera los nombres de colección). La función `_get_collection_and_resource_id()` en `milvus_multitenancy.py` implementa esta lógica.

**Si el frontend cambia cómo genera nombres de colección sin actualizar esta función, puede ocurrir mezcla de datos entre recursos.** Este es el riesgo más crítico de este diseño.

## Módulo

```
backend/server/retrieval/vector/dbs/milvus_multitenancy.py
```

## Relacionado

- [[Cinco colecciones Milvus]] — Las 5 colecciones y qué tipo de datos almacena cada una
- [[Aislamiento por resource_id]] — El mecanismo de aislamiento dentro de colecciones compartidas
- [[Milvus]] — El stack de base de datos vectorial
- [[MOC - Decisiones]] — D-05 en el índice de decisiones
- [[MOC - RAG y Búsqueda Vectorial]] — Índice del cluster de RAG
