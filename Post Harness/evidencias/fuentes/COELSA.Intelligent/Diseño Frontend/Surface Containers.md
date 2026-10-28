---
title: "Surface Containers"
type: referencia
tags: [coelsa-intelligent, diseño, surfaces, jerarquia-visual, tailwind]
aliases: [Surface containers COELSA, Niveles de superficie, Material surfaces]
description: "Usar cuando necesitás crear jerarquía visual entre elementos anidados en COELSA.Intelligent sin usar opacidad arbitraria."
estado: vigente
---

# Surface Containers

## Qué es

Material Design 3 define **5 niveles de superficie** para crear jerarquía visual. En el [[ECO Design System]] de COELSA.Intelligent, estos niveles se expresan con clases Tailwind `bg-surface-container-*`.

## Los 5 niveles

| Nivel | Clase Tailwind | Light | Dark | Uso semántico |
|-------|---------------|-------|------|---------------|
| **Lowest** | `bg-surface-container-lowest` | `#FFFFFF` | `#090F10` | Elementos embebidos sin énfasis; fondos de scroll |
| **Low** | `bg-surface-container-low` | `#EFF5F5` | `#171D1D` | Separación ligera; sidebar background |
| **Default** | `bg-surface-container` | `#E9EFEF` | `#1B2121` | Cards estándar; contenedor por defecto |
| **High** | `bg-surface-container-high` | `#E4E9EA` | `#252B2C` | Modals, dialogs; elementos destacados |
| **Highest** | `bg-surface-container-highest` | `#DEE3E4` | `#303637` | Tooltips, popovers; máximo foco |

## Patrón de uso correcto (jerarquía anidada)

```html
<!-- Fondo base de la pantalla -->
<div class="bg-surface text-on-surface min-h-screen">

  <!-- Card estándar -->
  <div class="bg-surface-container rounded-xl p-6">
    <h3 class="text-title-large text-on-surface">Título</h3>

    <!-- Sección más destacada dentro de la card -->
    <div class="bg-surface-container-high rounded-lg p-4 mt-4">
      Elemento con más énfasis
    </div>
  </div>

</div>
```

## Anti-patrones

- ❌ **No** usar `opacity-50` o `bg-black/10` para crear profundidad
- ❌ **No** saltar niveles (de `lowest` directo a `highest`)
- ❌ **No** usar valores hex de colores neutros directamente en componentes

## Relacionado

- [[Roles semánticos de color]] — Los roles de los que surface-container es parte
- [[ECO Design System]] — El sistema de diseño general
- [[Dark mode reglas]] — Cómo cambian los valores de surface en dark mode
- [[MOC - Diseño y Frontend]] — Índice del cluster de diseño
