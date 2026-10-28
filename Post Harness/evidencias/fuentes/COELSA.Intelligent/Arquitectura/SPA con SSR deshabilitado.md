---
title: "SPA con SSR deshabilitado"
type: decision
tags: [coelsa-intelligent, arquitectura, ssr, sveltekit, seguridad]
aliases: [SSR deshabilitado, SPA mode, ssr false]
description: "Usar cuando necesitás entender por qué la app es una SPA sin SSR, qué implica para seguridad, y por qué el CVE de markdown-it no aplica."
estado: vigente
---

# SPA con SSR deshabilitado

## Qué es

COELSA.Intelligent tiene el SSR (Server-Side Rendering) de [[SvelteKit 2]] **explícitamente deshabilitado**:

```javascript
// src/routes/+layout.js
export const ssr = false;
```

Esto convierte la aplicación en una **SPA pura**: el servidor solo sirve el HTML inicial y los assets; toda la lógica de renderizado corre en el navegador del cliente.

## Por qué está deshabilitado

Dos razones principales:

1. **Modelo de despliegue**: COELSA.Intelligent usa un backend FastAPI separado en otro proceso/contenedor. El SSR de SvelteKit requeriría que el propio servidor Node.js hiciera llamadas al backend durante el renderizado, complicando el modelo de despliegue en [[OpenShift]].

2. **Seguridad (CVE-2025-7969)**: La vulnerabilidad XSS de `markdown-it` afecta únicamente contextos SSR. Al tener SSR deshabilitado, este vector de ataque no existe. Ver [[CVE-2025-7969 markdown-it]].

## Implicaciones

- La app **no funciona sin JavaScript** en el cliente. No es un trade-off relevante para el caso de uso (chat corporativo interno).
- Los [[CSP con nonces|nonces CSP]] **no son compatibles** con el modo de desarrollo de SvelteKit (`npm run dev`), que genera scripts dinámicamente en el navegador. Los nonces solo se activan en OpenShift (`ENABLE_CSP_NONCES=true`).
- El build produce assets estáticos que se sirven desde el backend FastAPI como archivos estáticos.

## Relacionado

- [[SvelteKit 2]] — Framework frontend donde se configura el modo SPA
- [[CSP con nonces]] — Los nonces solo funcionan en producción por esta razón
- [[CVE-2025-7969 markdown-it]] — El CVE que no aplica gracias a este diseño
- [[MOC - Arquitectura]] — Contexto de la decisión dentro del sistema general
- [[Despliegue en OpenShift]] — Cómo se sirve la SPA compilada desde FastAPI
