---
title: "OpenShift"
type: stack
tags: [coelsa-intelligent, stack, openshift, despliegue, kubernetes]
aliases: [OpenShift COELSA, OCP COELSA]
description: "Usar cuando trabajás con el despliegue de COELSA.Intelligent en OpenShift: ConfigMaps, Routes, timeouts de HAProxy o escalado horizontal."
estado: vigente
---

# OpenShift

## Qué es

COELSA.Intelligent se despliega en **OpenShift** (Red Hat OpenShift Container Platform), la plataforma de orquestación de contenedores de COELSA. Los pipelines de CI/CD están en Azure DevOps.

## Entornos activos

| Entorno | Pipeline |
|---------|---------|
| DEV | `azure-pipeline-DEV.yml` |
| VALIDACION | `azure-pipeline-VALIDACION.yml` |
| PRODUCCIÓN | `azure-pipeline-PROD.yml` |
| Release management | `azure-pipeline-RELEASE.yml` |

## Requisitos de configuración

1. **ConfigMap**: variables de entorno de la app — `docs/OPENSHIFT-CONFIGMAP.yaml`
2. **Routes**: configuración de ingress con CSP — `docs/OPENSHIFT-ROUTE-CONFIG.yaml`
3. **Timeout de HAProxy**: debe ser mayor a **300 segundos** para soportar el procesamiento completo de archivos con RAG (embedding + inserción en Milvus puede superar 5 minutos en documentos grandes)

## Redis para escalado horizontal

Sin [[Redis]] como canal de WebSockets, escalar la app a múltiples pods haría que los eventos de socket no se propaguen entre instancias. Redis es requisito previo para escalar en OpenShift.

## CSP en el Route

La CSP se configura en la definición del Route. Para [[SharePoint OneDrive integración]], los dominios `login.microsoftonline.com` y `graph.microsoft.com` deben estar en la directiva `connect-src`. Ver [[CSP con nonces]].

## Relacionado

- [[Pipelines Azure DevOps]] — Los 4 pipelines que despliegan en OpenShift
- [[Despliegue en OpenShift]] — Pasos de despliegue paso a paso
- [[Redis]] — Requerido para escalar horizontalmente
- [[CSP con nonces]] — La CSP que vive en la configuración del Route
- [[MOC - Stack]] — Contexto de OpenShift en el stack completo
