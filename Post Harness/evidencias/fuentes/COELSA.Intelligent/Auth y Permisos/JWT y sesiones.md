---
title: "JWT y sesiones"
type: concepto
tags: [coelsa-intelligent, auth, jwt, sesiones, tokens]
aliases: [JWT COELSA, Tokens de sesión, HS256 COELSA]
description: "Usar cuando necesitás entender cómo se generan y validan los tokens de sesión internos de COELSA.Intelligent después del login con Azure AD."
estado: vigente
---

# JWT y sesiones

## Qué es

Después de un login OAuth exitoso con [[Azure AD OAuth|Azure AD]], COELSA.Intelligent genera un **JWT interno** (JSON Web Token) que el frontend usa en todas las requests subsiguientes. Este token es independiente del token de Azure AD.

## Especificaciones del token

- **Algoritmo**: HS256 (HMAC con SHA-256)
- **Clave secreta**: `WEBUI_SECRET_KEY` (variable de entorno)
- **Módulo**: `backend/server/utils/auth.py`

## Generación

```python
# Pseudocódigo del flujo
token = jwt.encode(
    {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=SESSION_HOURS)
    },
    SESSION_SECRET,  # WEBUI_SECRET_KEY
    algorithm=ALGORITHM  # HS256
)
```

## Validación

Cada endpoint protegido valida el token usando el `HTTPBearer` security scheme de FastAPI. El decorador `get_current_user` extrae el usuario del token y verifica que exista en la base de datos.

## Firma HMAC

Para verificación de webhooks entre servicios internos, existe una firma HMAC separada (`verify_signature()`) usando `TRUSTED_SIGNATURE_KEY`. Usa `hmac.compare_digest` para prevenir timing attacks.

## Relacionado

- [[Azure AD login exclusivo]] — El flujo OAuth que termina en la generación del JWT
- [[bcrypt para contraseñas]] — La otra pieza de auth; para contraseñas locales (deshabilitadas en COELSA)
- [[FastAPI y uvicorn]] — El servidor donde se registran las dependencias de validación
- [[MOC - Autenticación y Permisos]] — Índice del cluster de auth
