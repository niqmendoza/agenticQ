---
title: "Sistema de errores centralizado"
type: concepto
tags: [coelsa-intelligent, arquitectura, errores, backend, frontend]
aliases: [Jerarquía de excepciones, Error handling centralizado]
description: "Usar cuando necesitás entender cómo el backend devuelve errores de forma consistente o cómo el frontend los captura y muestra al usuario."
estado: vigente
---

# Sistema de errores centralizado

## Qué es

COELSA.Intelligent centraliza el manejo de excepciones en el backend con una jerarquía estándar de 10 tipos, y tiene componentes específicos en el frontend para cada categoría.

## Backend: tipos de excepción

Todos los errores devuelven un JSON consistente:

```json
{
  "message": "Mensaje legible para el usuario",
  "status_code": 400,
  "details": "Detalle técnico (omitido en producción)"
}
```

| Tipo | Código HTTP | Uso |
|------|-------------|-----|
| `BadRequest` | 400 | Input inválido |
| `Unauthorized` | 401 | Token ausente o inválido |
| `Forbidden` | 403 | Sin permiso para el recurso |
| `NotFound` | 404 | Recurso inexistente |
| `Conflict` | 409 | Estado incompatible (ej: email duplicado) |
| `Validation` | 422 | Fallo de validación de esquema |
| `RateLimit` | 429 | Rate limit excedido |
| `InternalServer` | 500 | Error interno inesperado |
| `ServiceUnavailable` | 503 | Servicio externo no disponible |
| `GatewayTimeout` | 504 | Timeout en llamada a servicio externo |

Los detalles técnicos se omiten en producción para no exponer información interna.

## Frontend: componentes de error

| Componente | Cuándo se muestra |
|------------|-------------------|
| `NetworkError.svelte` | Sin conexión o error de red |
| `TimeoutError.svelte` | La request tomó demasiado tiempo |
| `GenericError.svelte` | Cualquier error no categorizado |
| `ErrorBoundary.svelte` | Envuelve secciones para capturar errores en render |

El archivo `src/routes/+error.svelte` recibe todos los códigos HTTP y rutea al componente correspondiente, incluyendo un fallback genérico.

## Relacionado

- [[Manejo de errores frontend]] — Detalle de los componentes Svelte de error
- [[FastAPI y uvicorn]] — El servidor donde se registran los handlers de excepción
- [[MOC - Arquitectura]] — Contexto del diseño de errores en el sistema
- [[Roles de usuario]] — Los errores 403 se disparan cuando el rol no alcanza
