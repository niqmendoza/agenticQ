---
title: "Internacionalización i18n"
type: concepto
tags: [coelsa-intelligent, diseño, i18n, traducciones, es-ar]
aliases: [i18n COELSA, Traducciones COELSA, i18next COELSA]
description: "Usar cuando necesitás agregar o modificar traducciones en COELSA.Intelligent, o cuando querés entender qué idiomas están soportados y cómo configurarlos."
estado: vigente
---

# Internacionalización i18n

## Qué es

COELSA.Intelligent usa **i18next** como sistema de internacionalización. Los archivos de traducción están en `src/lib/i18n/` organizados por código de idioma.

## Idiomas soportados

| Código | Idioma | Estado |
|--------|--------|--------|
| `es-AR` | Castellano Rioplatense | **Default** — ver [[Idioma por defecto es-AR]] |
| `en-GB` | English (British) | Activo |
| `pt-BR` | Português (Brasil) | Activo |

## Idiomas eliminados del fork

Removidos en v1.3.0: `es-ES`, `pt-PT`, `en-US`. Ver [[Idioma por defecto es-AR]].

## Configuración

```env
DEFAULT_LOCALE=es-AR
```

En el frontend, el idioma también puede seleccionarse por usuario en Settings (acceso restringido según [[Roles de usuario]]).

## Uso en componentes Svelte

```svelte
<script>
  import { t } from '$lib/i18n';
</script>

<button>{$t('common.send')}</button>
<p>{$t('chat.placeholder', { name: userName })}</p>
```

## Agregar una traducción

1. Localizar la clave en `src/lib/i18n/es-AR.json` (o crear si no existe)
2. Agregar la misma clave en `en-GB.json` y `pt-BR.json`
3. Usar `$t('clave')` en el componente Svelte

## Relacionado

- [[Idioma por defecto es-AR]] — La decisión de elegir es-AR como default
- [[SvelteKit 2]] — El framework donde se integra i18next
- [[MOC - Diseño y Frontend]] — Índice del cluster de diseño
