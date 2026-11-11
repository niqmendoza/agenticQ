---
title: "Idioma por defecto es-AR"
type: decision
tags: [coelsa-intelligent, arquitectura, i18n, localizacion]
aliases: [es-AR default, Castellano Rioplatense COELSA, Localización COELSA]
description: "Usar cuando necesitás saber qué idiomas soporta COELSA.Intelligent, cuál es el default y cuáles fueron eliminados del fork."
estado: vigente
---

# Idioma por defecto es-AR

## Qué es

COELSA.Intelligent tiene configurado **Castellano Rioplatense (`es-AR`)** como idioma por defecto de la interfaz.

```env
DEFAULT_LOCALE=es-AR
```

## Idiomas disponibles

| Idioma | Código | Estado |
|--------|--------|--------|
| Castellano Rioplatense | `es-AR` | **Activo — default** |
| English (British) | `en-GB` | Activo |
| Português (Brasil) | `pt-BR` | Activo |

## Idiomas eliminados del fork

Los siguientes idiomas fueron removidos porque no aplican al contexto corporativo de COELSA:

- `es-ES` — Castellano de España (reemplazado por es-AR)
- `pt-PT` — Portugués de Portugal (reemplazado por pt-BR)
- `en-US` — Inglés americano (reemplazado por en-GB)

## Sistema de i18n

El sistema de internacionalización usa `i18next`. Los archivos de traducción están en `src/lib/i18n/`. Ver [[Internacionalización i18n]] para el detalle de cómo se usa en componentes.

## Relacionado

- [[Internacionalización i18n]] — Detalle técnico del sistema de traducciones
- [[Fork de Open WebUI]] — El upstream usaba en-US como default; este es uno de los cambios del fork
- [[MOC - Arquitectura]] — Contexto de la decisión de localización
- [[MOC - Decisiones]] — D-18 en el índice de decisiones
