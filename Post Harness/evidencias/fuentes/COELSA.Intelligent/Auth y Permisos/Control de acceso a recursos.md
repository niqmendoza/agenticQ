---
title: "Control de acceso a recursos"
type: concepto
tags: [coelsa-intelligent, auth, access-control, knowledge, files]
aliases: [access_control, Permisos de recursos, Resource access control]
description: "Usar cuando necesitás entender cómo se controla quién puede leer o escribir un recurso (Knowledge base o File) en COELSA.Intelligent."
estado: vigente
---

# Control de acceso a recursos

## Qué es

Los modelos `Knowledge` y `File` tienen un campo `access_control` en formato JSON que define quién puede leer y escribir ese recurso. El campo `None` significa acceso público para todos los `user`.

## Modos de acceso

| Valor de `access_control` | Significado |
|--------------------------|-------------|
| `None` | Acceso público — cualquier usuario con rol `user` puede leer |
| `{}` (objeto vacío) | Acceso privado — solo el propietario puede acceder |
| Objeto con reglas | Acceso custom — según grupos y usuarios específicos |

## Estructura del objeto custom

```json
{
  "read": {
    "group_ids": ["grupo-id-1", "grupo-id-2"],
    "user_ids": ["user-id-1"]
  },
  "write": {
    "group_ids": [],
    "user_ids": ["user-id-admin"]
  }
}
```

## Evaluación de acceso

La función `has_access()` en `backend/server/utils/access_control.py` evalúa si un usuario tiene permiso sobre un recurso. La evaluación verifica:
1. Si el usuario es el propietario → acceso total
2. Si el usuario tiene rol `admin` → acceso total
3. Si el `access_control` es `None` → acceso de lectura para `user`
4. Si hay reglas custom → verifica `group_ids` y `user_ids`

## Relacionado

- [[Roles de usuario]] — El rol del usuario es el primer criterio de la evaluación
- [[Grupos y permisos]] — Los `group_ids` en access_control referencian grupos del sistema
- [[MOC - Autenticación y Permisos]] — Índice del cluster de auth
