---
title: "Tipografía Saira"
type: referencia
tags: [coelsa-intelligent, diseño, tipografia, saira, fuentes]
aliases: [Fuente Saira, Saira font, Typography COELSA]
description: "Usar cuando necesitás usar la tipografía correcta en componentes de COELSA.Intelligent o entender las clases tipográficas disponibles."
estado: vigente
---

# Tipografía Saira

## Qué es

**Saira** es la fuente corporativa de COELSA.Intelligent. Es una fuente sans-serif variable con distintos pesos, definida con `@font-face` en `src/tailwind.css` y cargada desde los assets locales de la app.

## Carga de la fuente

```css
/* src/tailwind.css */
@font-face {
  font-family: 'Saira';
  src: url('/assets/fonts/Saira-VariableFont.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;
}
```

Los archivos de fuente están en `static/assets/fonts/`.

## Clases tipográficas (Material Design 3)

Las clases tipográficas siguiendo la escala de Material Design 3 están definidas en `src/app.css`:

| Clase | Uso semántico |
|-------|--------------|
| `text-display-large` | Títulos hero muy grandes |
| `text-display-medium` | Títulos hero medianos |
| `text-headline-large` | Encabezados de sección principales |
| `text-headline-medium` | Encabezados de sección secundarios |
| `text-title-large` | Títulos de card o dialog |
| `text-title-medium` | Subtítulos |
| `text-body-large` | Cuerpo de texto principal |
| `text-body-medium` | Cuerpo de texto secundario |
| `text-label-large` | Etiquetas de botón |
| `text-label-small` | Chips, badges |

## Configuración Tailwind

La fuente Saira está registrada en `tailwind.config.js` como `font-sans` por defecto, por lo que todos los elementos usan Saira automáticamente sin necesidad de clases adicionales.

## Relacionado

- [[ECO Design System]] — El sistema de diseño donde vive la tipografía
- [[Roles semánticos de color]] — Las clases de color que se combinan con la tipografía
- [[MOC - Diseño y Frontend]] — Índice del cluster de diseño
