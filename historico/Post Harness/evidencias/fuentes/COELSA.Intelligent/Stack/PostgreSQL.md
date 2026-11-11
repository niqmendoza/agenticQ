---
title: "PostgreSQL"
type: stack
tags: [coelsa-intelligent, stack, postgresql, base-de-datos, sqlalchemy]
aliases: [PostgreSQL stack, BD relacional COELSA]
description: "Usar cuando necesitás configurar o diagnosticar la conexión a PostgreSQL, entender los modelos SQLAlchemy o ejecutar migraciones Alembic."
estado: vigente
---

# PostgreSQL

## Qué es

COELSA.Intelligent usa **PostgreSQL 14+** como base de datos relacional principal. El acceso se hace a través de **SQLAlchemy** como ORM y **Alembic** para migraciones de esquema.

## Versión mínima

PostgreSQL **14** — requerido por el uso de funciones JSON y de ventana.

## Configuración

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/coelsa_intelligent
```

## Modelos principales

| Tabla | Archivo | Descripción |
|-------|---------|-------------|
| `user` | `models/users.py` | Usuarios con rol, email, oauth_sub, settings |
| `chat` | `models/chats.py` | Conversaciones con JSON del historial |
| `file` | `models/files.py` | Metadatos de archivos subidos; `chat_id` para cascada |
| `knowledge` | `models/knowledge.py` | Bases de conocimiento con access_control |
| `group` | `models/groups.py` | Grupos con permisos JSON |
| `config` | `config.py` | Configuración persistente de la app |

## Migraciones

Las migraciones se gestionan con Alembic. El servidor las aplica automáticamente al iniciar (`run_migrations()` en `config.py`). Ver [[Migraciones Alembic]] para el flujo manual.

## Relacionado

- [[PostgreSQL como base de datos]] — La decisión de migrar de SQLite a PostgreSQL
- [[Migraciones Alembic]] — Cómo gestionar cambios de esquema
- [[Borrado en cascada de archivos]] — El campo `chat_id` en `file` que habilita la cascada
- [[MOC - Stack]] — Contexto de PostgreSQL en el stack completo
