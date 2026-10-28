---
title: "Migraciones Alembic"
type: referencia
tags: [coelsa-intelligent, desarrollo, alembic, migraciones, postgresql]
aliases: [Alembic migrations, Database migrations COELSA]
description: "Usar cuando necesitás agregar una migración de base de datos, aplicar migraciones pendientes o entender el flujo de gestión de esquema en COELSA.Intelligent."
estado: vigente
---

# Migraciones Alembic

## Qué es

COELSA.Intelligent usa **Alembic** para gestionar los cambios de esquema de [[PostgreSQL]]. Las migraciones están en `backend/server/migrations/`.

## Arranque automático

Al iniciar el servidor, `run_migrations()` en `config.py` aplica automáticamente las migraciones pendientes:

```python
# backend/server/config.py
def run_migrations():
    from alembic import command
    from alembic.config import Config
    alembic_cfg = Config(SERVER_DIR / "alembic.ini")
    command.upgrade(alembic_cfg, "head")
```

## Comandos manuales

```bash
# Aplicar todas las migraciones pendientes
cd backend
alembic upgrade head

# Ver el estado actual
alembic current

# Ver el historial de migraciones
alembic history

# Crear una nueva migración (autogenerada)
alembic revision --autogenerate -m "descripcion_del_cambio"

# Crear una migración manual vacía
alembic revision -m "descripcion_del_cambio"
```

## Convención de nombres

Los archivos de migración siguen el patrón: `<revision_id>_<descripcion>.py`

Ejemplo: `add_minio_file_fields.sql` (también hay migraciones SQL directas en `backend/migrations/`).

## Cuándo ejecutar

- Antes del primer arranque en un entorno nuevo
- Después de cada deploy que incluya cambios de esquema
- Los pipelines de CI/CD deben ejecutar `alembic upgrade head` como parte del proceso de deploy

## Relacionado

- [[PostgreSQL]] — La base de datos que gestionan las migraciones
- [[PostgreSQL como base de datos]] — Por qué se usa PostgreSQL (y Alembic)
- [[Despliegue en OpenShift]] — Las migraciones como parte del flujo de deploy
- [[MOC - Desarrollo]] — Índice del cluster de desarrollo
