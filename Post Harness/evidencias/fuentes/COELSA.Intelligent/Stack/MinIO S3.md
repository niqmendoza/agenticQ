---
title: "MinIO S3"
type: stack
tags: [coelsa-intelligent, stack, minio, s3, almacenamiento]
aliases: [MinIO, S3 COELSA, Object storage COELSA]
description: "Usar cuando necesitás configurar MinIO, entender cómo se suben archivos a S3 o diagnosticar problemas de conectividad con el bucket."
estado: vigente
---

# MinIO S3

## Qué es

COELSA.Intelligent usa **MinIO** (o cualquier endpoint S3-compatible) para el almacenamiento persistente de archivos subidos por usuarios. El acceso a los archivos se hace siempre mediante [[URLs firmadas MinIO|URLs firmadas (presigned URLs)]].

## Variables de entorno

```env
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_NAME=coelsa-intelligent
S3_ENDPOINT_URL=http://minio:9000
FILE_STORAGE_CLEANUP_DAYS=30
```

## Configuración de boto3 (timeouts)

La configuración de `boto3` está ajustada para entornos Windows y redes corporativas:
- Connect timeout: **30 segundos**
- Read timeout: **120 segundos**
- Reintentos: **10** con backoff exponencial
- TCP keepalive: habilitado

Esto resolvió el problema de timeouts en uploads desde Windows documentado en el CHANGELOG v1.3.0.

## Creación del bucket

Para crear el bucket en un entorno nuevo:

```bash
python scripts/create_minio_bucket.py
```

El script lee la configuración desde `backend/server/config.py`, que auto-carga `.env`. Ejecutar desde la raíz del proyecto.

## Proveedores soportados

El sistema soporta múltiples providers a través de la interfaz `StorageProvider`. Ver [[Agregar proveedor de almacenamiento]] para cómo agregar nuevos backends (GCS, Azure Blob Storage, etc.).

## Relacionado

- [[Sistema híbrido de almacenamiento]] — El flujo completo local → MinIO
- [[URLs firmadas MinIO]] — Cómo se generan las URLs de acceso
- [[Scheduler de limpieza]] — El job que elimina archivos vencidos del bucket
- [[Agregar proveedor de almacenamiento]] — Cómo implementar un provider alternativo
- [[MOC - Stack]] — Contexto de MinIO en el stack completo
