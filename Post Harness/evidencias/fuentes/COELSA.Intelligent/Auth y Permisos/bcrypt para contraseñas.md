---
title: "bcrypt para contraseñas"
type: decision
tags: [coelsa-intelligent, auth, bcrypt, seguridad, contraseñas]
aliases: [bcrypt COELSA, Migración de passlib, Hashing de contraseñas]
description: "Usar cuando necesitás entender por qué se usa bcrypt directamente en lugar de passlib y cuál era el bug que motivó el cambio."
estado: vigente
---

# bcrypt para contraseñas

## Qué es

COELSA.Intelligent usa la librería **`bcrypt`** nativa de Python para el hashing de contraseñas, en lugar de `passlib.CryptContext` que usaba el upstream.

```python
# backend/server/utils/auth.py
import bcrypt

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
```

## Por qué se migró de passlib

`passlib.CryptContext` no manejaba correctamente el **límite de 72 bytes de bcrypt** en la codificación UTF-8 interna. El problema se manifestaba al crear usuarios incluso con contraseñas cortas — el error aparecía por cómo `passlib` gestionaba internamente la codificación, no por la longitud de la contraseña.

El reemplazo por `bcrypt` nativo resuelve esto porque:
1. Maneja explícitamente la codificación `utf-8` al llamar a `encode()`
2. No tiene la capa de abstracción de `passlib` que introducía el bug

## Contexto

Aunque COELSA.Intelligent tiene el login local deshabilitado (ver [[Azure AD login exclusivo]]), el código de autenticación por contraseña sigue existente en el backend para usos internos (API keys, etc.) y como fallback en caso de que el login local se rehabilite en el futuro.

## Relacionado

- [[Azure AD login exclusivo]] — El login local está deshabilitado; este código existe como fallback
- [[JWT y sesiones]] — El token que se genera después de una autenticación exitosa
- [[MOC - Autenticación y Permisos]] — Índice del cluster de auth
- [[MOC - Decisiones]] — D-07 en el índice de decisiones
