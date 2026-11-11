---
title: "COELSA.Intelligent - Indice Maestro OKF"
type: index
tags: [coelsa-intelligent, okf, indice, navegacion-llm]
aliases: [Indice Maestro, OKF Index, Entry Point LLM]
description: "Usar cuando un LLM o una persona necesita encontrar rapido la nota exacta sin recorrer todo el vault."
estado: vigente
---

# COELSA.Intelligent - Indice Maestro OKF

Indice de navegacion global para acceso por salto directo a cada nota del segundo cerebro.

## Como usar este indice (LLM-first)

1. Elegi la seccion por dominio (Arquitectura, Seguridad, RAG, etc.).
2. Abri solo 1 nota candidata y valida relevancia por `description` del frontmatter.
3. Si falta contexto, segui enlaces a MOC del dominio antes de leer mas notas.

## Router rapido por intencion

- Panorama general del sistema: [COELSA.Intelligent - Home](COELSA.Intelligent%20-%20Home.md)
- Ver el mapa por dominios: [MOC - Decisiones](MOCs/MOC%20-%20Decisiones.md)
- Arquitectura base del fork: [MOC - Arquitectura](MOCs/MOC%20-%20Arquitectura.md)
- Stack tecnologico y componentes: [MOC - Stack](MOCs/MOC%20-%20Stack.md)
- Login, roles, sesiones y permisos: [MOC - Autenticación y Permisos](MOCs/MOC%20-%20Autenticación%20y%20Permisos.md)
- Carga/almacenamiento de archivos: [MOC - Almacenamiento](MOCs/MOC%20-%20Almacenamiento.md)
- Retrieval, Milvus y aislamiento: [MOC - RAG y Búsqueda Vectorial](MOCs/MOC%20-%20RAG%20y%20Búsqueda%20Vectorial.md)
- Routing de modelos y tooling IA: [MOC - Modelos IA y Routing](MOCs/MOC%20-%20Modelos%20IA%20y%20Routing.md)
- UI, design system y componentes Svelte: [MOC - Diseño y Frontend](MOCs/MOC%20-%20Diseño%20y%20Frontend.md)
- Hardening y vulnerabilidades: [MOC - Seguridad](MOCs/MOC%20-%20Seguridad.md)
- Build, pipeline y despliegue: [MOC - CI-CD y Despliegue](MOCs/MOC%20-%20CI-CD%20y%20Despliegue.md)
- Patrones y tareas de desarrollo: [MOC - Desarrollo](MOCs/MOC%20-%20Desarrollo.md)

## Catalogo completo por carpeta

### Raiz

- [COELSA.Intelligent - Home](COELSA.Intelligent%20-%20Home.md)

### MOCs

- [MOC - Almacenamiento](MOCs/MOC%20-%20Almacenamiento.md)
- [MOC - Arquitectura](MOCs/MOC%20-%20Arquitectura.md)
- [MOC - Autenticación y Permisos](MOCs/MOC%20-%20Autenticación%20y%20Permisos.md)
- [MOC - CI-CD y Despliegue](MOCs/MOC%20-%20CI-CD%20y%20Despliegue.md)
- [MOC - Decisiones](MOCs/MOC%20-%20Decisiones.md)
- [MOC - Desarrollo](MOCs/MOC%20-%20Desarrollo.md)
- [MOC - Diseño y Frontend](MOCs/MOC%20-%20Diseño%20y%20Frontend.md)
- [MOC - Modelos IA y Routing](MOCs/MOC%20-%20Modelos%20IA%20y%20Routing.md)
- [MOC - RAG y Búsqueda Vectorial](MOCs/MOC%20-%20RAG%20y%20Búsqueda%20Vectorial.md)
- [MOC - Seguridad](MOCs/MOC%20-%20Seguridad.md)
- [MOC - Stack](MOCs/MOC%20-%20Stack.md)

### Arquitectura

- [Fork de Open WebUI](Arquitectura/Fork%20de%20Open%20WebUI.md)
- [Headers de usuario COELSA](Arquitectura/Headers%20de%20usuario%20COELSA.md)
- [Idioma por defecto es-AR](Arquitectura/Idioma%20por%20defecto%20es-AR.md)
- [PostgreSQL como base de datos](Arquitectura/PostgreSQL%20como%20base%20de%20datos.md)
- [Redis para WebSockets](Arquitectura/Redis%20para%20WebSockets.md)
- [Sistema de errores centralizado](Arquitectura/Sistema%20de%20errores%20centralizado.md)
- [SPA con SSR deshabilitado](Arquitectura/SPA%20con%20SSR%20deshabilitado.md)

### Stack

- [Azure AD OAuth](Stack/Azure%20AD%20OAuth.md)
- [FastAPI y uvicorn](Stack/FastAPI%20y%20uvicorn.md)
- [LiteLLM proxy](Stack/LiteLLM%20proxy.md)
- [Milvus](Stack/Milvus.md)
- [MinIO S3](Stack/MinIO%20S3.md)
- [Ollama](Stack/Ollama.md)
- [OpenShift](Stack/OpenShift.md)
- [PostgreSQL](Stack/PostgreSQL.md)
- [Redis](Stack/Redis.md)
- [SvelteKit 2](Stack/SvelteKit%202.md)

### Auth y Permisos

- [Azure AD login exclusivo](Auth%20y%20Permisos/Azure%20AD%20login%20exclusivo.md)
- [bcrypt para contraseñas](Auth%20y%20Permisos/bcrypt%20para%20contraseñas.md)
- [Control de acceso a recursos](Auth%20y%20Permisos/Control%20de%20acceso%20a%20recursos.md)
- [Grupos y permisos](Auth%20y%20Permisos/Grupos%20y%20permisos.md)
- [JWT y sesiones](Auth%20y%20Permisos/JWT%20y%20sesiones.md)
- [Roles de usuario](Auth%20y%20Permisos/Roles%20de%20usuario.md)

### Almacenamiento

- [Borrado en cascada de archivos](Almacenamiento/Borrado%20en%20cascada%20de%20archivos.md)
- [Flujo de subida de archivos](Almacenamiento/Flujo%20de%20subida%20de%20archivos.md)
- [Scheduler de limpieza](Almacenamiento/Scheduler%20de%20limpieza.md)
- [Sistema híbrido de almacenamiento](Almacenamiento/Sistema%20híbrido%20de%20almacenamiento.md)
- [Storage Dashboard](Almacenamiento/Storage%20Dashboard.md)
- [URLs firmadas MinIO](Almacenamiento/URLs%20firmadas%20MinIO.md)

### RAG

- [Aislamiento por resource_id](RAG/Aislamiento%20por%20resource_id.md)
- [Chats de referencia](RAG/Chats%20de%20referencia.md)
- [Cinco colecciones Milvus](RAG/Cinco%20colecciones%20Milvus.md)
- [Milvus multi-tenancy](RAG/Milvus%20multi-tenancy.md)
- [Módulo de retrieval](RAG/Módulo%20de%20retrieval.md)

### Modelos IA

- [Cadena SearXNG Context Forge](Modelos%20IA/Cadena%20SearXNG%20Context%20Forge.md)
- [MCP y tool calling](Modelos%20IA/MCP%20y%20tool%20calling.md)
- [PyTorch CPU-only](Modelos%20IA/PyTorch%20CPU-only.md)
- [Routing de modelos IA](Modelos%20IA/Routing%20de%20modelos%20IA.md)
- [SharePoint OneDrive integración](Modelos%20IA/SharePoint%20OneDrive%20integración.md)
- [Validación de urlIdx](Modelos%20IA/Validación%20de%20urlIdx.md)

### Diseño Frontend

- [Dark mode reglas](Diseño%20Frontend/Dark%20mode%20reglas.md)
- [ECO Design System](Diseño%20Frontend/ECO%20Design%20System.md)
- [Internacionalización i18n](Diseño%20Frontend/Internacionalización%20i18n.md)
- [Manejo de errores frontend](Diseño%20Frontend/Manejo%20de%20errores%20frontend.md)
- [Patrones de componentes Svelte](Diseño%20Frontend/Patrones%20de%20componentes%20Svelte.md)
- [Roles semánticos de color](Diseño%20Frontend/Roles%20semánticos%20de%20color.md)
- [Surface Containers](Diseño%20Frontend/Surface%20Containers.md)
- [Tipografía Saira](Diseño%20Frontend/Tipografía%20Saira.md)
- [Tokens primitivos de color](Diseño%20Frontend/Tokens%20primitivos%20de%20color.md)

### Seguridad

- [CSP con nonces](Seguridad/CSP%20con%20nonces.md)
- [CVE-2025-7969 markdown-it](Seguridad/CVE-2025-7969%20markdown-it.md)
- [Dependencias vulnerables](Seguridad/Dependencias%20vulnerables.md)
- [Hardening ReDoS](Seguridad/Hardening%20ReDoS.md)
- [Path Traversal](Seguridad/Path%20Traversal.md)
- [Protección SSRF](Seguridad/Protección%20SSRF.md)
- [Riesgos de seguridad aceptados](Seguridad/Riesgos%20de%20seguridad%20aceptados.md)

### CI-CD

- [Build frontend](CI-CD/Build%20frontend.md)
- [Despliegue en OpenShift](CI-CD/Despliegue%20en%20OpenShift.md)
- [Dockerfile](CI-CD/Dockerfile.md)
- [Pipelines Azure DevOps](CI-CD/Pipelines%20Azure%20DevOps.md)
- [SSL corporativo en build](CI-CD/SSL%20corporativo%20en%20build.md)

### Desarrollo

- [Agregar proveedor de almacenamiento](Desarrollo/Agregar%20proveedor%20de%20almacenamiento.md)
- [Agregar router REST](Desarrollo/Agregar%20router%20REST.md)
- [Ejecución local](Desarrollo/Ejecución%20local.md)
- [Loguru y logging](Desarrollo/Loguru%20y%20logging.md)
- [Migraciones Alembic](Desarrollo/Migraciones%20Alembic.md)
- [Patrones frontend críticos](Desarrollo/Patrones%20frontend%20críticos.md)

## Cobertura

- Total de notas indexadas: 79
- Cobertura: 100% de los archivos `.md` detectados en el vault al 2026-07-08