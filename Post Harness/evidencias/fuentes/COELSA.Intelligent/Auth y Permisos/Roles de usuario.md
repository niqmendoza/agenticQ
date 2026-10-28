---
title: "Roles de usuario"
type: concepto
tags: [coelsa-intelligent, auth, roles, permisos]
aliases: [User roles, Roles COELSA, admin user pending]
description: "Usar cuando necesitás saber qué puede hacer un usuario según su rol en COELSA.Intelligent o cuándo restringir acceso a una funcionalidad."
estado: vigente
---

# Roles de usuario

## Qué es

COELSA.Intelligent define tres roles de usuario, almacenados en el campo `role` del modelo `User`:

| Rol | Descripción | Capacidades principales |
|-----|-------------|------------------------|
| `admin` | Administrador del sistema | Acceso total; gestión de usuarios, grupos, modelos, configuración |
| `user` | Usuario activo | Chat, upload de archivos, uso de bases de conocimiento según permisos |
| `pending` | En espera de aprobación | Solo puede ver la pantalla de espera; no puede usar el chat |

## Estado `pending`

Un usuario recién logeado por primera vez via Azure AD puede quedar en estado `pending` si la configuración requiere aprobación manual. Un admin debe cambiar el rol a `user` para habilitar el acceso.

## Restricciones por rol en la UI

En la vista de **Settings**, las siguientes tabs están restringidas a `admin`:
- **Personalization** — configuración visual de la app
- **Audio** — configuración de síntesis y transcripción de voz

Los usuarios `user` ven estas tabs pero no pueden acceder a su contenido.

## Funcionalidades deshabilitadas para todos los roles

Independientemente del rol, estas funcionalidades están desactivadas en el fork:
- Sugerencias de chat automáticas
- Ejecución de Python en CodeBlocks
- Webhooks en la sección Account

## Relacionado

- [[Grupos y permisos]] — Permisos granulares dentro del rol `user`
- [[Control de acceso a recursos]] — Cómo el rol interactúa con el access_control de recursos
- [[Azure AD login exclusivo]] — Cómo se asigna el rol inicial al primer login
- [[MOC - Autenticación y Permisos]] — Índice del cluster de auth
