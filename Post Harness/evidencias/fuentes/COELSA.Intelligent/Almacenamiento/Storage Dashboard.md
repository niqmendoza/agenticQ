---
title: "Storage Dashboard"
type: concepto
tags: [coelsa-intelligent, almacenamiento, monitoreo, admin, dashboard]
aliases: [Storage status endpoint, Dashboard de almacenamiento]
description: "Usar cuando necesitás monitorear el uso del almacenamiento en COELSA.Intelligent o diagnosticar el estado de MinIO desde la API."
estado: vigente
---

# Storage Dashboard

## Qué es

El **Storage Dashboard** es un conjunto de endpoints de monitoreo que expone métricas de uso del almacenamiento de COELSA.Intelligent. Requiere rol `admin`.

## Endpoints

```
GET /api/v1/storage/status
```

Retorna:
- Espacio total y usado en MinIO
- Número de objetos en el bucket
- Número de archivos registrados en la BD
- Archivos locales pendientes de migración
- Archivos huérfanos detectados
- Estadísticas de antigüedad de archivos

## Router

El router está en `backend/server/routers/storage_management.py`. Los endpoints delegan a `StorageProvider.get_storage_stats()` para obtener las métricas del provider activo.

## Acceso

Solo usuarios con rol `admin` pueden acceder a estos endpoints. Un usuario con rol `user` recibirá un error `403 Forbidden`. Ver [[Roles de usuario]].

## Relacionado

- [[Sistema híbrido de almacenamiento]] — El sistema que se monitorea
- [[MinIO S3]] — El provider que reporta las estadísticas
- [[Roles de usuario]] — El rol admin requerido para acceder
- [[MOC - Almacenamiento]] — Índice del cluster de almacenamiento
