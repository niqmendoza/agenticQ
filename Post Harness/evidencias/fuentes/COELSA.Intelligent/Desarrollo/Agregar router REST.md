---
title: "Agregar router REST"
type: referencia
tags: [coelsa-intelligent, desarrollo, backend, fastapi, routers, api]
aliases: [Agregar endpoint, Nuevo router FastAPI, New REST endpoint]
description: "Usar cuando necesitás agregar un nuevo grupo de endpoints REST al backend de COELSA.Intelligent — pasos concretos para crear y registrar un router."
estado: vigente
---

# Agregar router REST

## Qué es

Guía paso a paso para agregar un nuevo conjunto de endpoints REST al backend de COELSA.Intelligent usando el patrón de routers de FastAPI.

## Pasos

### 1. Crear el módulo del router

```python
# backend/server/routers/mi_nuevo_router.py
from fastapi import APIRouter, Depends, HTTPException
from server.models.users import UserModel
from server.utils.auth import get_current_user

router = APIRouter()

@router.get("/")
async def get_items(user: UserModel = Depends(get_current_user)):
    """Endpoint de ejemplo."""
    return {"items": []}

@router.post("/")
async def create_item(
    data: dict,
    user: UserModel = Depends(get_current_user)
):
    return {"created": True}
```

### 2. Importar el router en `main.py`

```python
# backend/server/main.py
from server.routers import (
    # ... routers existentes ...
    mi_nuevo_router,  # Agregar aquí
)
```

### 3. Registrar el router en la app

```python
# backend/server/main.py — en la función que monta los routers
app.include_router(
    mi_nuevo_router.router,
    prefix="/api/v1/mi-recurso",
    tags=["mi-recurso"]
)
```

## Convenciones

- Los routers usan el prefijo `/api/v1/`
- Todos los endpoints que requieren autenticación usan `Depends(get_current_user)`
- Los errores usan la jerarquía del [[Sistema de errores centralizado]]
- La lógica de acceso a BD va en `backend/server/models/`; el router solo orquesta

## Relacionado

- [[FastAPI y uvicorn]] — El servidor donde se montan los routers
- [[Sistema de errores centralizado]] — Las excepciones que deben usarse en los endpoints
- [[Control de acceso a recursos]] — Cómo agregar control de acceso a nivel de endpoint
- [[MOC - Desarrollo]] — Índice del cluster de desarrollo
