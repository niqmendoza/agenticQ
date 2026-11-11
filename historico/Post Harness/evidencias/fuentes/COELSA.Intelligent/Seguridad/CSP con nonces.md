---
title: "CSP con nonces"
type: concepto
tags: [coelsa-intelligent, seguridad, csp, nonces, openshift]
aliases: [Content Security Policy, CSP nonces COELSA, NonceInjectionMiddleware]
description: "Usar cuando necesitás entender la configuración de Content Security Policy de COELSA.Intelligent, por qué los nonces no funcionan en dev, o cómo se configura en OpenShift."
estado: vigente
---

# CSP con nonces

## Qué es

COELSA.Intelligent usa **nonces de Content Security Policy (CSP)** en producción (OpenShift) para eliminar `'unsafe-inline'` de la directiva `script-src`. El middleware `NonceInjectionMiddleware` genera un nonce único por request.

## Configuración por entorno

| Entorno | `ENABLE_CSP_NONCES` | `script-src` |
|---------|---------------------|-------------|
| Localhost / dev | `false` (obligatorio) | `'unsafe-inline'` (requerido por SvelteKit dev) |
| OpenShift | `true` | `'nonce-{valor}'` (sin unsafe-inline) |

**Importante**: `ENABLE_CSP_NONCES=true` en desarrollo **rompe la app**. SvelteKit en modo dev genera scripts dinámicamente en el browser; el nonce se inyecta en el HTML del servidor antes de que esos scripts existan, por lo que no coinciden.

## Cómo funciona en OpenShift

Con `ENABLE_CSP_NONCES=true`:
1. `NonceInjectionMiddleware` genera un valor aleatorio criptográficamente seguro por request
2. El nonce se inyecta en todos los `<script>` tags del HTML devuelto
3. El header `Content-Security-Policy` incluye `'nonce-{valor}'` en `script-src`
4. `'unsafe-inline'` se elimina automáticamente de `script-src`

El nonce se regenera en **cada request** (no es reutilizable).

## Dominio CSP para SharePoint

Para que [[SharePoint OneDrive integración]] funcione, la CSP del Route debe incluir:
```
connect-src: login.microsoftonline.com graph.microsoft.com
```

Ver `docs/OPENSHIFT-ROUTE-CONFIG.yaml`.

## Estado de alertas ZAP

| Alerta | Estado |
|--------|--------|
| `script-src unsafe-inline` | ✅ Resuelta — nonces implementados |
| `style-src unsafe-inline` | ⚠️ No resoluble sin refactoring profundo |
| `script-src unsafe-eval` | ⚠️ Riesgo aceptado — ver [[Riesgos de seguridad aceptados]] |

## Relacionado

- [[SPA con SSR deshabilitado]] — Por qué los nonces no funcionan en dev
- [[Despliegue en OpenShift]] — Donde se activa ENABLE_CSP_NONCES
- [[Riesgos de seguridad aceptados]] — Los riesgos CSP aceptados
- [[MOC - Seguridad]] — Índice del cluster de seguridad
