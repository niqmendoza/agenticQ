---
title: "Ejecución local"
type: referencia
tags: [coelsa-intelligent, desarrollo, local, dev, comandos]
aliases: [Dev local COELSA, Correr localmente, Local setup]
description: "Usar cuando necesitás levantar COELSA.Intelligent en tu máquina local para desarrollo — comandos exactos para frontend y backend."
estado: vigente
---

# Ejecución local

## Qué es

Guía de referencia para levantar COELSA.Intelligent en modo desarrollo local.

## Prerrequisitos

Tener corriendo localmente (o con Docker):
- [[PostgreSQL]] 14+ en `localhost:5432`
- [[Redis]] 7+ en `localhost:6379`
- [[Milvus]] 2.4+ en `localhost:19530`
- [[MinIO S3]] en `localhost:9000` (opcional; puede usarse storage local)
- [[Ollama]] o [[LiteLLM proxy]] para los modelos IA

## Configuración inicial

```bash
# 1. Copiar y editar variables de entorno
cp .env.example .env

# 2. Editar .env con las conexiones locales y credenciales de Azure AD
```

Variables mínimas requeridas: ver `docs/setup.md`.

## Levantar el backend

```bash
cd backend
pip install -r requirements.txt  # Primera vez

# Linux / macOS
./dev.sh

# Windows
start_windows.bat
```

El backend queda disponible en `http://localhost:8080` con **hot-reload** activado.

## Levantar el frontend

```bash
# Primera vez
npm install

npm run dev
```

El frontend queda disponible en `http://localhost:5173`. Apunta automáticamente al backend en `localhost:8080`.

## Notas de desarrollo

- Los [[CSP con nonces|nonces CSP]] deben estar deshabilitados en local (`ENABLE_CSP_NONCES=false`)
- Los logs del backend usan loguru — ver [[Loguru y logging]]
- Para probar el storage S3, configurar `STORAGE_PROVIDER=s3` con las vars de [[MinIO S3]]
- Las migraciones se aplican automáticamente al arrancar el backend — ver [[Migraciones Alembic]]

## Relacionado

- [[FastAPI y uvicorn]] — El backend que se levanta con dev.sh
- [[SvelteKit 2]] — El frontend que se levanta con npm run dev
- [[CSP con nonces]] — Por qué ENABLE_CSP_NONCES debe ser false en local
- [[MOC - Desarrollo]] — Índice del cluster de desarrollo
