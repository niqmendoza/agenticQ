---
title: "Grupos y permisos"
type: concepto
tags: [coelsa-intelligent, auth, grupos, permisos]
aliases: [Groups COELSA, Permisos de grupo]
description: "Usar cuando necesitás entender cómo se organizan los permisos granulares por grupo en COELSA.Intelligent o cómo crear/gestionar grupos de usuarios."
estado: vigente
---

# Grupos y permisos

## Qué es

Además del sistema de [[Roles de usuario|roles]], COELSA.Intelligent implementa **grupos** con permisos granulares en formato JSON. Los grupos permiten dar acceso diferenciado a conjuntos de funcionalidades a subconjuntos de usuarios.

## Modelo de datos (Group)

```python
class Group(Base):
    id: Text           # UUID
    user_id: Text      # Creador del grupo
    name: Text
    description: Text
    data: JSON         # Datos adicionales
    meta: JSON         # Metadatos internos
    permissions: JSON  # Permisos del grupo
    user_ids: JSON     # Lista de IDs de usuarios en el grupo
    created_at: BigInteger
    updated_at: BigInteger
```

## Estructura del JSON de permisos

Los permisos se definen como un objeto JSON con capacidades específicas. Ejemplo:

```json
{
  "chat": {
    "file_upload": true,
    "web_search": false
  },
  "workspace": {
    "models": false,
    "knowledge": true
  }
}
```

## Permisos por defecto

La configuración de permisos iniciales para nuevos usuarios y grupos se ajustó en v1.3.0 a las necesidades corporativas de COELSA (ver CHANGELOG). Los defaults del upstream no aplicaban al contexto corporativo.

## Relacionado

- [[Roles de usuario]] — El rol es la primera capa; los grupos son la segunda capa granular
- [[Control de acceso a recursos]] — Cómo los grupos interactúan con el access_control de Knowledge y Files
- [[MOC - Autenticación y Permisos]] — Índice del cluster de auth
