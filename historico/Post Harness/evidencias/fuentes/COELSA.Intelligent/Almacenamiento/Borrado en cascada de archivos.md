---
title: "Borrado en cascada de archivos"
type: concepto
tags: [coelsa-intelligent, almacenamiento, cascada, archivos, chats]
aliases: [Cascade delete files, Eliminación en cascada]
description: "Usar cuando necesitás entender qué pasa con los archivos de MinIO cuando se elimina un chat en COELSA.Intelligent."
estado: vigente
---

# Borrado en cascada de archivos

## Qué es

Cuando un usuario **elimina una conversación (chat)**, COELSA.Intelligent elimina automáticamente todos los archivos asociados a esa conversación, tanto en la base de datos como en [[MinIO S3]].

## Por qué existe

Sin esta funcionalidad, eliminar un chat dejaría archivos huérfanos en MinIO indefinidamente. A largo plazo, esto genera acumulación de storage sin posibilidad de recuperarlo sin una migración manual.

## Implementación

El modelo `File` tiene una columna `chat_id` (con índice):

```python
class File(Base):
    chat_id = Column(String, nullable=True, index=True)
    # Vinculación con chats para borrado en cascada
```

Cuando el endpoint de eliminación de chat se ejecuta:
1. Busca todos los registros `File` donde `chat_id == chat.id`
2. Para cada archivo: llama a `StorageProvider.delete_file(file.path)`
3. Elimina los registros de la tabla `file`
4. Elimina el registro del chat

## Diferencia con el Scheduler

| Mecanismo | Cuándo actúa | Qué elimina |
|-----------|-------------|-------------|
| **Borrado en cascada** | Al eliminar un chat | Archivos del chat eliminado |
| **[[Scheduler de limpieza]]** | Diariamente | Huérfanos + archivos vencidos |

Ambos mecanismos son complementarios.

## Relacionado

- [[Sistema híbrido de almacenamiento]] — El sistema del que la cascada es parte
- [[Scheduler de limpieza]] — El mecanismo diario de limpieza de archivos
- [[MinIO S3]] — El storage donde se eliminan los objetos
- [[MOC - Almacenamiento]] — Índice del cluster de almacenamiento
