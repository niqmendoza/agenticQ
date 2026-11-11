---
title: "MOC — Almacenamiento"
type: moc
tags: [coelsa-intelligent, almacenamiento, minio, moc]
aliases: [MOC Almacenamiento, Storage COELSA]
description: "Usar cuando trabajás con subida, acceso, limpieza o monitoreo de archivos en COELSA.Intelligent — cubre el sistema híbrido local+MinIO."
estado: vigente
---

# MOC — Almacenamiento

El almacenamiento de archivos sigue un flujo híbrido: primero local, luego migrado a [[MinIO S3]]. El acceso siempre se hace con [[URLs firmadas MinIO|URLs firmadas]].

## Notas de este cluster

- [[Sistema híbrido de almacenamiento]] — Visión general del flujo local → MinIO y cómo coexisten los dos providers
- [[Flujo de subida de archivos]] — Ciclo completo: recepción → guardado local → scheduler → MinIO
- [[URLs firmadas MinIO]] — Cómo se generan presigned URLs para acceso seguro temporal
- [[Scheduler de limpieza]] — Job diario que elimina archivos huérfanos y vencidos (`FILE_STORAGE_CLEANUP_DAYS`)
- [[Borrado en cascada de archivos]] — Al eliminar un chat se eliminan sus archivos en MinIO automáticamente
- [[Storage Dashboard]] — Endpoint `/api/v1/storage/status`; métricas de uso para administradores

## MOCs vecinos

- [[MOC - Stack]] — MinIO S3 como componente del stack de almacenamiento
- [[MOC - Arquitectura]] — Decisión de diseño del sistema híbrido y el scheduler
- [[MOC - Autenticación y Permisos]] — El Storage Dashboard requiere rol `admin`
- [[MOC - CI-CD y Despliegue]] — Variables de entorno S3 que deben estar en el ConfigMap de OpenShift
