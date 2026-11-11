---
title: "Scheduler de limpieza"
type: concepto
tags: [coelsa-intelligent, almacenamiento, scheduler, limpieza, archivos]
aliases: [Cleanup scheduler, Job de limpieza, FILE_STORAGE_CLEANUP_DAYS]
description: "Usar cuando necesitás entender qué archivos elimina el scheduler diario, cómo se configura el umbral de antigüedad y cómo funciona la migración automática a MinIO."
estado: vigente
---

# Scheduler de limpieza

## Qué es

COELSA.Intelligent tiene un **scheduler que corre diariamente** y realiza dos tareas sobre el almacenamiento:
1. **Migra** archivos desde almacenamiento local a [[MinIO S3]]
2. **Elimina** archivos huérfanos (sin registro en BD) y archivos que superan el umbral de antigüedad

## Configuración

```env
FILE_STORAGE_CLEANUP_DAYS=30
```

Con este valor, los archivos que no han sido accedidos en más de 30 días son candidatos para eliminación. El campo `last_accessed_at` del modelo `File` registra el último acceso.

## Qué es un archivo huérfano

Un archivo **huérfano** es aquel que:
- Existe físicamente en el almacenamiento (local o MinIO)
- **No tiene** un registro correspondiente en la tabla `file` de la base de datos

Esto puede ocurrir si un upload falló a medias o si un registro fue eliminado manualmente de la BD sin limpiar el storage.

## Cuándo se ejecuta

El scheduler es un job asíncrono que se registra durante el `lifespan` de la aplicación FastAPI. No tiene una hora fija; se ejecuta cada 24 horas a partir del arranque del servidor.

## Relacionado

- [[Sistema híbrido de almacenamiento]] — El sistema del que el scheduler es parte
- [[MinIO S3]] — El destino de los archivos migrados
- [[Borrado en cascada de archivos]] — La otra vía de eliminación de archivos (cuando se borra el chat)
- [[MOC - Almacenamiento]] — Índice del cluster de almacenamiento
