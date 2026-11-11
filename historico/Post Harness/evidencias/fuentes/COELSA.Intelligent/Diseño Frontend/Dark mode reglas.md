---
title: "Dark mode reglas"
type: concepto
tags: [coelsa-intelligent, diseño, dark-mode, tema, colores]
aliases: [Dark mode COELSA, Modo oscuro, Inversión de roles]
description: "Usar cuando implementás o verificás el comportamiento de dark mode en componentes de COELSA.Intelligent — especialmente para entender qué cambia y qué no."
estado: vigente
---

# Dark mode reglas

## Qué es

El dark mode de COELSA.Intelligent **invierte los roles semánticos**, no los colores primitivos. La escala Teal sigue siendo Teal; solo cambia qué tono de la escala se asigna a cada rol.

## La regla fundamental

```
Light mode: primary = teal-40 (#006972, oscuro)
Dark mode:  primary = teal-80 (#57D8E6, claro)
```

Los primitivos no cambian; cambia qué primitivo se asigna a qué rol.

## Anti-patrones de dark mode

| Anti-patrón | Por qué está mal |
|------------|-----------------|
| Usar escala directa (`bg-teal-40`) | No se invierte en dark mode |
| Asumir que `text-on-primary` es siempre blanco | En dark mode `on-primary` = teal-20 (oscuro) |
| Hardcodear `text-white` sobre `bg-primary` | Rompe en light mode si se ajustan los roles |
| Usar `opacity-50` para el texto secundario | Debe usarse `text-on-surface/75` (opacity utility) |

## Implementación técnica

Las CSS custom properties se definen en `src/lib/styles/colors.css` con dos bloques:

```css
/* Light mode (por defecto) */
:root {
  --color-primary: #006972;
  --color-on-primary: #FFFFFF;
  /* ... */
}

/* Dark mode */
[data-theme="dark"], .dark {
  --color-primary: #57D8E6;
  --color-on-primary: #00363B;
  /* ... */
}
```

Tailwind usa estas variables via `tailwind.config.js`.

## Surface containers en dark mode

Los [[Surface Containers]] más oscuros en light mode son los más claros en dark mode. La jerarquía se mantiene: `highest` siempre es el más destacado, solo cambia si eso significa "más claro" o "más oscuro".

## Relacionado

- [[Roles semánticos de color]] — Los roles que se invierten en dark mode
- [[Tokens primitivos de color]] — Los valores que no cambian
- [[Surface Containers]] — Cómo cambian los niveles de superficie en dark mode
- [[ECO Design System]] — El sistema general de diseño
