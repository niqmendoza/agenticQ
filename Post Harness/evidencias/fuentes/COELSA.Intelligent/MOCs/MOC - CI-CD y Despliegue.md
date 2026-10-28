---
title: "MOC — CI-CD y Despliegue"
type: moc
tags: [coelsa-intelligent, cicd, openshift, docker, moc]
aliases: [MOC CICD, CI-CD COELSA, Despliegue COELSA]
description: "Usar cuando trabajás con pipelines de Azure DevOps, el Dockerfile, el build del frontend o el despliegue en OpenShift de COELSA.Intelligent."
estado: vigente
---

# MOC — CI-CD y Despliegue

El ciclo de vida de versiones pasa por 4 pipelines de Azure DevOps (DEV → VALIDACION → PROD → RELEASE). El runtime es [[OpenShift]] con imágenes construidas en Docker.

## Notas de este cluster

- [[Pipelines Azure DevOps]] — Los 4 pipelines y sus responsabilidades: DEV, VALIDACION, PROD, RELEASE
- [[Dockerfile]] — CPU-only PyTorch; sin Pyodide; workarounds de SSL corporativo
- [[Build frontend]] — Diferencia entre `npm run build` (con Pyodide) y `npm run build:docker` (sin Pyodide, para CI)
- [[SSL corporativo en build]] — Por qué `NODE_TLS_REJECT_UNAUTHORIZED=0` está en el Dockerfile y qué riesgo implica
- [[Despliegue en OpenShift]] — ConfigMap, Routes, timeout de HAProxy, creación del bucket MinIO

## MOCs vecinos

- [[MOC - Stack]] — Las tecnologías que se contienerizan y despliegan
- [[MOC - Seguridad]] — El riesgo de SSL deshabilitado en build es un riesgo aceptado
- [[MOC - Desarrollo]] — Qué comandos de build usar en cada contexto (dev vs CI)
- [[MOC - Almacenamiento]] — El bucket MinIO debe crearse antes del primer despliegue
