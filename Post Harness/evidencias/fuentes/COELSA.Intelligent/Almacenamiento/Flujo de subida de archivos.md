---
title: "Flujo de subida de archivos"
type: concepto
tags: [coelsa-intelligent, almacenamiento, upload, archivos]
aliases: [File upload flow, Subida de archivos COELSA]
description: "Usar cuando necesitás rastrear el ciclo de vida de un archivo subido por un usuario, desde la recepción HTTP hasta su almacenamiento en MinIO."
estado: vigente
---

# Flujo de subida de archivos

## Qué es

Describe el ciclo completo desde que un usuario sube un archivo hasta que queda accesible via URL firmada en MinIO.

## Pasos del flujo

### 1. Recepción (router `files.py`)
El endpoint `POST /api/v1/files/` recibe el archivo multipart. El backend:
- Sanitiza el nombre del archivo (protección contra [[Path Traversal]])
- Guarda temporalmente en `data/uploads/<uuid>-<filename>`
- Crea un registro en la tabla `file` con `path` = ruta local

### 2. Procesamiento RAG (opcional)
Si el archivo va a ser embedido (Knowledge base, búsqueda vectorial):
- Se procesa con los loaders del [[Módulo de retrieval]]
- Los chunks se insertan en [[Milvus]] bajo la colección correspondiente

### 3. Migración a MinIO (scheduler diario)
El [[Scheduler de limpieza|scheduler]] ejecuta diariamente:
- Lee los registros de `file` con `path` local
- Sube cada archivo a [[MinIO S3]]
- Actualiza el campo `path` en BD con la clave S3
- Genera una [[URLs firmadas MinIO|URL firmada]] para el acceso

### 4. Acceso
Al solicitar un archivo, el backend:
- Verifica [[Control de acceso a recursos|access_control]]
- Si el path es S3: genera una URL firmada con expiración configurable
- Si el path es local: sirve el archivo directamente

## Relacionado

- [[Sistema híbrido de almacenamiento]] — El modelo general del que este flujo es parte
- [[URLs firmadas MinIO]] — Cómo se generan las URLs de acceso
- [[Scheduler de limpieza]] — El job que ejecuta la migración y la limpieza
- [[Borrado en cascada de archivos]] — Qué pasa cuando se elimina el chat asociado
- [[Protección SSRF]] — La sanitización de paths en el paso de recepción
