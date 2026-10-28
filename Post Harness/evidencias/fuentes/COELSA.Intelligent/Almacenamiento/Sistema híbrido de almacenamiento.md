---
title: "Sistema híbrido de almacenamiento"
type: concepto
tags: [coelsa-intelligent, almacenamiento, minio, s3, hibrido]
aliases: [Almacenamiento híbrido, Local+S3, Hybrid storage]
description: "Usar cuando necesitás entender el flujo completo de archivos en COELSA.Intelligent: cómo pasan de local a MinIO y cómo coexisten los dos providers."
estado: vigente
---

# Sistema híbrido de almacenamiento

## Qué es

El almacenamiento de archivos en COELSA.Intelligent opera en modo **híbrido**: los archivos se reciben localmente y luego se migran a [[MinIO S3]]. Los archivos viejos y los nuevos coexisten hasta que el scheduler los migra.

## Flujo completo

```
Usuario sube archivo
       ↓
Backend guarda en data/uploads/ (local temporal)
       ↓
[Scheduler diario] detecta archivos locales
       ↓
Migra a MinIO → genera presigned URL
       ↓
Actualiza metadatos en BD (path = s3://bucket/key)
       ↓
[Acceso futuro] devuelve URL firmada de MinIO
```

## Proveedores disponibles

La interfaz `StorageProvider` (en `backend/server/storage/provider.py`) es abstracta. Las implementaciones concretas son:
- `LocalStorageProvider` — guarda en `data/uploads/`
- `S3StorageProvider` (MinIO / AWS S3)
- `GCSStorageProvider` (Google Cloud Storage)
- `AzureBlobStorageProvider` (Azure Blob Storage)

La variable `STORAGE_PROVIDER` en `.env` selecciona el provider activo.

## Fallback local

Si MinIO no está disponible, el sistema usa el almacenamiento local. Esto permite desarrollo local sin configurar MinIO, aunque los archivos no persisten en caso de recreación del contenedor.

## Script de migración

Para migrar archivos existentes a MinIO en un entorno ya en producción:

```bash
python scripts/migrate_to_minio.py
```

## Relacionado

- [[Flujo de subida de archivos]] — El ciclo completo de recepción y migración de un archivo
- [[MinIO S3]] — El provider S3 que recibe los archivos migrados
- [[URLs firmadas MinIO]] — Cómo se accede a los archivos en MinIO
- [[Scheduler de limpieza]] — El job que limpia archivos vencidos
- [[Agregar proveedor de almacenamiento]] — Cómo implementar un nuevo provider
