---
title: "Azure AD OAuth"
type: stack
tags: [coelsa-intelligent, stack, azure-ad, oauth, openid-connect]
aliases: [Azure AD, OAuth COELSA, OpenID Connect COELSA]
description: "Usar cuando necesitás configurar o diagnosticar la autenticación OAuth con Azure AD en COELSA.Intelligent."
estado: vigente
---

# Azure AD OAuth

## Qué es

COELSA.Intelligent usa **Azure Active Directory** como único proveedor de identidad, implementado mediante el protocolo **OAuth 2.0 / OpenID Connect**. El registro local de usuarios y el formulario de login con usuario/contraseña están deshabilitados. Ver [[Azure AD login exclusivo]].

## Variables de entorno requeridas

```env
OAUTH_CLIENT_ID=<azure-client-id>
OAUTH_CLIENT_SECRET=<azure-client-secret>
OAUTH_PROVIDER_NAME=microsoft
OPENID_PROVIDER_URL=https://login.microsoftonline.com/<tenant-id>/v2.0/.well-known/openid-configuration
```

## Flujo de autenticación

1. El usuario hace clic en "Login con Microsoft".
2. Es redirigido a `login.microsoftonline.com` para autenticarse.
3. Azure AD devuelve un código de autorización al callback del backend.
4. El backend intercambia el código por tokens (access + id token).
5. El `sub` del id token se guarda como `oauth_sub` en el modelo `User`.
6. Se genera un JWT interno (ver [[JWT y sesiones]]) que el frontend usa en todas las requests.

## Para SharePoint / OneDrive

La misma App Registration de Azure AD puede usarse para el [[SharePoint OneDrive integración|File Picker de SharePoint]], pero requiere el permiso adicional `Files.Read.All`.

## CSP

El dominio `login.microsoftonline.com` debe estar incluido en la CSP del Route de OpenShift para que el redirect funcione. Ver [[CSP con nonces]] y [[Despliegue en OpenShift]].

## Relacionado

- [[Azure AD login exclusivo]] — La decisión de arquitectura de deshabilitar el login local
- [[JWT y sesiones]] — El token interno que se genera después de OAuth
- [[SharePoint OneDrive integración]] — Extensión del mismo Azure AD para File Picker
- [[MOC - Stack]] — Contexto del proveedor de identidad en el stack completo
