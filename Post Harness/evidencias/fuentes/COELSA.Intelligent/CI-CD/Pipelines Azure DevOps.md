---
title: "Pipelines Azure DevOps"
type: referencia
tags: [coelsa-intelligent, cicd, azure-devops, pipelines, openshift]
aliases: [Azure DevOps pipelines, CI/CD COELSA, Pipelines COELSA]
description: "Usar cuando necesitás entender qué hace cada pipeline de CI/CD de COELSA.Intelligent o cuándo se ejecuta cada uno."
estado: vigente
---

# Pipelines Azure DevOps

## Qué es

COELSA.Intelligent tiene **4 pipelines de Azure DevOps** que gestionan el ciclo de vida completo desde el commit hasta producción.

## Los 4 pipelines

| Archivo | Entorno | Propósito |
|---------|---------|-----------|
| `azure-pipeline-DEV.yml` | DEV | Build y deploy automático de ramas de feature |
| `azure-pipeline-VALIDACION.yml` | VALIDACION | Build y deploy para QA/testing |
| `azure-pipeline-PROD.yml` | PRODUCCIÓN | Deploy a producción (requiere aprobación) |
| `azure-pipeline-RELEASE.yml` | — | Gestión de versiones (tagging, changelogs) |

## Pasos típicos de un pipeline

1. **Build frontend**: `npm run build:docker` (sin Pyodide — ver [[Build frontend]])
2. **Build imagen Docker**: `docker build -t ...` (ver [[Dockerfile]])
3. **Push a registry**: push de la imagen al registro corporativo
4. **Deploy a OpenShift**: `oc apply` con la nueva imagen

## Variables críticas de entorno en los pipelines

Las variables de entorno de la app **no** están hardcodeadas en los pipelines. Se inyectan desde:
- **ConfigMap de OpenShift**: variables de aplicación — ver [[Despliegue en OpenShift]]
- **Azure DevOps Variable Groups**: credenciales (secrets) del pipeline

## Relacionado

- [[Build frontend]] — El comando `build:docker` que usan los pipelines
- [[Dockerfile]] — La imagen que construyen los pipelines
- [[Despliegue en OpenShift]] — El destino de los deploys
- [[MOC - CI-CD y Despliegue]] — Índice del cluster de CI/CD
