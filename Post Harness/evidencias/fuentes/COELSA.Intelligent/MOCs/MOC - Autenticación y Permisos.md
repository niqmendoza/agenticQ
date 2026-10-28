---
title: "MOC — Autenticación y Permisos"
type: moc
tags: [coelsa-intelligent, autenticacion, permisos, moc]
aliases: [MOC Autenticación, Auth COELSA, Permisos COELSA]
description: "Usar cuando trabajás con login, roles, grupos, tokens o control de acceso a recursos en COELSA.Intelligent."
estado: vigente
---

# MOC — Autenticación y Permisos

Todo acceso al sistema pasa por [[Azure AD login exclusivo]]. Los [[Roles de usuario]] y [[Grupos y permisos]] determinan qué puede hacer cada usuario dentro de la aplicación.

## Notas de este cluster

- [[Azure AD login exclusivo]] — Solo OAuth Azure AD; registro local y formulario de usuario deshabilitados
- [[Roles de usuario]] — Los tres roles: `admin`, `user`, `pending`; qué puede hacer cada uno
- [[Grupos y permisos]] — Modelo de grupos con JSON de permisos granulares; acceso por grupo o usuario
- [[JWT y sesiones]] — Generación y validación de tokens HS256; `WEBUI_SECRET_KEY`
- [[bcrypt para contraseñas]] — Por qué se migró de passlib a bcrypt nativo; problema de truncación UTF-8
- [[Control de acceso a recursos]] — Campo `access_control` en Knowledge y Files; modos public/private/custom

## MOCs vecinos

- [[MOC - Arquitectura]] — Decisión de usar Azure AD exclusivo como parte del diseño del fork
- [[MOC - Seguridad]] — CSP, SSRF y otras remediaciones que complementan la autenticación
- [[MOC - Diseño y Frontend]] — Cómo se restringen tabs de Settings solo para admin en la UI
