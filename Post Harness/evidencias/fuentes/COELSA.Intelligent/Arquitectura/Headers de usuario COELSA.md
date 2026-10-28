---
title: "Headers de usuario COELSA"
type: concepto
tags: [coelsa-intelligent, arquitectura, http-headers]
aliases: [Encabezados HTTP COELSA, X-COELSA headers]
description: "Usar cuando necesitás saber cómo se identifica al usuario actual en las requests HTTP entre componentes internos de COELSA.Intelligent."
estado: vigente
---

# Headers de usuario COELSA

## Qué es

COELSA.Intelligent renombró los encabezados HTTP que propagan la identidad del usuario autenticado entre componentes. La convención es:

```
X-COELSA.Intelligent-User-*
```

Estos headers viajan en las requests del proxy y del middleware de autenticación hacia los servicios internos.

## Por qué el renombre

El upstream Open WebUI usaba nombres de header genéricos. El renombre hace que el origen de los headers sea inequívoco en logs y en reglas de seguridad de red, y evita colisiones con otros sistemas que puedan pasar headers similares.

## Uso

Los headers se inyectan automáticamente por el middleware de autenticación al validar el token JWT. Los routers que necesitan la identidad del usuario usan el sistema estándar de dependencias de FastAPI (`get_current_user`) en lugar de leer los headers directamente.

## Relacionado

- [[JWT y sesiones]] — El token JWT que valida la sesión antes de inyectar estos headers
- [[FastAPI y uvicorn]] — El servidor donde el middleware de auth corre
- [[Azure AD login exclusivo]] — La fuente de identidad que genera estos headers
- [[MOC - Arquitectura]] — Contexto de la convención en el sistema
