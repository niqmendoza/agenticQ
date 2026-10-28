---
title: "Azure AD login exclusivo"
type: decision
tags: [coelsa-intelligent, auth, azure-ad, autenticacion]
aliases: [Solo Azure AD, Login corporativo COELSA]
description: "Usar cuando necesitás confirmar que el login local está deshabilitado o cuando configurás un nuevo entorno y necesitás saber qué variables de Azure AD son obligatorias."
estado: vigente
---

# Azure AD login exclusivo

## Qué es

COELSA.Intelligent tiene **deshabilitados** el registro de nuevos usuarios vía formulario web y el login con email/contraseña. El **único** medio de autenticación es Azure Active Directory via OAuth 2.0.

## Qué está deshabilitado

- Formulario de registro de usuario (el endpoint existe pero rechaza requests)
- Login con email + contraseña
- Auto-signup (creación automática de cuenta al primer login configurada en modo restringido)

## Por qué esta decisión

COELSA es una empresa con Azure AD como directorio corporativo. Usar Azure AD:
- Unifica la gestión de usuarios con el directorio existente
- Elimina la necesidad de gestionar contraseñas en la aplicación
- Permite aprovechar políticas de seguridad (MFA, Conditional Access) del tenant corporativo
- Cumple con las políticas de seguridad de TI de COELSA

## Variables requeridas

```env
OAUTH_CLIENT_ID=<azure-client-id>
OAUTH_CLIENT_SECRET=<azure-client-secret>
OAUTH_PROVIDER_NAME=microsoft
OPENID_PROVIDER_URL=https://login.microsoftonline.com/<tenant-id>/v2.0/.well-known/openid-configuration
```

## Relacionado

- [[Azure AD OAuth]] — Detalle técnico de la configuración OAuth
- [[JWT y sesiones]] — El token interno que se genera después del OAuth exitoso
- [[Roles de usuario]] — Los roles que se asignan a los usuarios una vez autenticados
- [[MOC - Autenticación y Permisos]] — Índice del cluster de auth
- [[MOC - Decisiones]] — D-11 en el índice de decisiones
