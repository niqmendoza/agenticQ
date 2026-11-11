---
title: "COELSA.Intelligent — Home"
type: home
tags: [coelsa-intelligent, home, indice]
aliases: [Home COELSA, COELSA Intelligent Home, COELSA.Intelligent Home]
description: "Usar cuando necesitás orientarte en el vault de COELSA.Intelligent — punto de entrada a todos los MOCs y áreas del proyecto."
estado: vigente
---

# COELSA.Intelligent — Home

Plataforma interna de chat con IA generativa de COELSA. Fork de Open WebUI adaptado para infraestructura corporativa: autenticación Azure AD, almacenamiento MinIO/S3, búsqueda vectorial Milvus, identidad visual COELSA y despliegue en OpenShift.

**Versión actual:** v1.3.0
**Entornos activos:** DEV · VALIDACION · PRODUCCIÓN (OpenShift)
**Repo base:** Fork de Open WebUI (MIT); cambios aplicados sobre versión estabilizada sin seguimiento del upstream.

> **Para LLMs:** cada nota tiene un campo `description` tipo "Usar cuando…" en el frontmatter YAML. Leer ese campo es suficiente para saber si la nota es relevante antes de leer el cuerpo completo.

> **Acceso rápido global:** [[OKF-INDEX]] para navegar por salto directo a cualquier nota del vault.

---

## Invariantes del proyecto (reglas que nunca se rompen)

- La autenticación es **exclusivamente Azure AD**; el registro local y el formulario de login están deshabilitados.
- **Teal (`#06ABB9`) es el color primario COELSA** en ambos temas (light y dark). Pink es solo acento decorativo.
- SSR está deshabilitado (`export const ssr = false`); la app es una SPA pura.
- No se mantiene compatibilidad directa con el upstream Open WebUI; los cambios se aplican deliberadamente.
- Todo par texto/fondo debe cumplir WCAG AA (4.5:1 texto normal, 3:1 texto grande).
- No hardcodear valores hex en componentes; usar siempre roles/tokens semánticos del ECO Design System.

---

## Mapas de Contenido (MOCs)

| Área | MOC | Qué agrupa |
|------|-----|-----------|
| Arquitectura general | [[MOC - Arquitectura]] | Decisiones de diseño estructural del sistema |
| Tecnologías del stack | [[MOC - Stack]] | Cada tecnología y su configuración |
| Autenticación y acceso | [[MOC - Autenticación y Permisos]] | Azure AD, roles, JWT, control de acceso |
| Almacenamiento de archivos | [[MOC - Almacenamiento]] | MinIO/S3, flujo de archivos, limpieza |
| RAG y búsqueda vectorial | [[MOC - RAG y Búsqueda Vectorial]] | Milvus, embeddings, retrieval, multi-tenancy |
| Modelos IA y routing | [[MOC - Modelos IA y Routing]] | Ollama, LiteLLM, MCP, SharePoint |
| Diseño visual y frontend | [[MOC - Diseño y Frontend]] | ECO Design System, colores, componentes |
| Seguridad y hardening | [[MOC - Seguridad]] | CSP, ReDoS, SSRF, dependencias |
| CI/CD y despliegue | [[MOC - CI-CD y Despliegue]] | Pipelines, Docker, OpenShift |
| Patrones de desarrollo | [[MOC - Desarrollo]] | Patrones críticos, migraciones, dev local |
| Decisiones indexadas | [[MOC - Decisiones]] | Índice de todas las decisiones de diseño |
