---
title: "Fork de Open WebUI"
type: decision
tags: [coelsa-intelligent, arquitectura, fork, open-webui]
aliases: [Open WebUI fork, Base del fork]
description: "Usar cuando necesitás entender qué es COELSA.Intelligent, de dónde viene y por qué no se sigue el upstream Open WebUI directamente."
estado: vigente
---

# Fork de Open WebUI

## Qué es

COELSA.Intelligent es un fork interno de [Open WebUI](https://github.com/open-webui/open-webui), una plataforma de chat con IA generativa de código abierto (licencia MIT). El fork se tomó sobre una versión base estabilizada y los cambios se aplican deliberadamente sobre esa base.

**No se mantiene compatibilidad directa con el upstream.** Esto significa que las actualizaciones del proyecto original no se incorporan automáticamente; cualquier cambio relevante del upstream debe evaluarse y portarse manualmente.

## Qué cambia respecto al upstream

| Área | Upstream (Open WebUI) | COELSA.Intelligent |
|------|----------------------|-------------------|
| Base de datos | SQLite (default) | [[PostgreSQL]] |
| Autenticación | Múltiples proveedores + registro local | Solo [[Azure AD OAuth]] |
| Almacenamiento | Local (`data/uploads/`) | Híbrido local + [[MinIO S3]] |
| Búsqueda vectorial | Una colección por recurso | [[Milvus multi-tenancy]] (5 colecciones) |
| Identidad visual | Open WebUI branding | [[ECO Design System]] COELSA |
| Idioma por defecto | `en-US` | `es-AR` |
| Despliegue | Docker genérico | [[OpenShift]] + Azure DevOps |

## Por qué no se sigue el upstream

El upstream evoluciona rápido y no está optimizado para las restricciones corporativas de COELSA (Azure AD, OpenShift, proxy corporativo, identidad visual propia). Mantener sincronización con el upstream requeriría resolver conflictos continuamente en áreas que COELSA deliberadamente modificó. La decisión es mantener una versión estabilizada y hacer cherry-pick de mejoras puntuales cuando sea necesario.

## Relacionado

- [[MOC - Arquitectura]] — Índice de todas las decisiones del fork
- [[SPA con SSR deshabilitado]] — Otra decisión de arquitectura que diverge del upstream
- [[PostgreSQL como base de datos]] — Primera y más importante migración de infraestructura
- [[ECO Design System]] — El rebranding visual completo que diferencia el fork
- [[MOC - Decisiones]] — Índice completo de decisiones con justificaciones
