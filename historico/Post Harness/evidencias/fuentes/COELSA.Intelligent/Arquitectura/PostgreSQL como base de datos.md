---
title: "PostgreSQL como base de datos"
type: decision
tags: [coelsa-intelligent, arquitectura, postgresql, base-de-datos]
aliases: [Migración a PostgreSQL, PostgreSQL decision]
description: "Usar cuando necesitás entender por qué se usa PostgreSQL en lugar de SQLite y cómo se gestiona el esquema con Alembic."
estado: vigente
---

# PostgreSQL como base de datos

## Qué es

El upstream Open WebUI usa SQLite por defecto. COELSA.Intelligent **migró a PostgreSQL** para soportar múltiples workers concurrentes, backups corporativos y el modelo de despliegue en [[OpenShift]].

## Configuración

```env
DATABASE_URL=postgresql://user:pass@host:5432/coelsa_intelligent
```

El esquema se gestiona con **Alembic**. Las migraciones están en `backend/server/migrations/`. El servidor ejecuta `alembic upgrade head` automáticamente al arrancar (via `run_migrations()` en `config.py`).

## Por qué PostgreSQL

- SQLite no admite múltiples writers concurrentes; con uvicorn en múltiples workers genera errores de lock.
- PostgreSQL tiene soporte corporativo, backup integrado con las herramientas de COELSA, y funcionalidades como JSON columns (usadas en varios modelos).
- La versión mínima requerida es **14+** por el uso de `json_agg` y funciones de ventana.

## Stack de acceso a datos

- **ORM**: SQLAlchemy (con `get_db()` como context manager de sesión)
- **Migraciones**: Alembic (ver [[Migraciones Alembic]])
- **Modelos**: `backend/server/models/` — User, Chat, File, Knowledge, Group, Memory, etc.

## Relacionado

- [[PostgreSQL]] — Nota de stack con versiones y configuración de conexión
- [[Migraciones Alembic]] — Cómo gestionar cambios de esquema
- [[MOC - Arquitectura]] — Contexto de la decisión en el sistema
- [[MOC - Decisiones]] — D-02 en el índice de decisiones
- [[Redis para WebSockets]] — La otra pieza de infraestructura de persistencia del sistema
