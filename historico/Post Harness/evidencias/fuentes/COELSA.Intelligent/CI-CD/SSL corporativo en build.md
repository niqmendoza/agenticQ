---
title: "SSL corporativo en build"
type: referencia
tags: [coelsa-intelligent, cicd, ssl, docker, seguridad, riesgo]
aliases: [SSL deshabilitado build, Corporate SSL proxy, TLS bypass build]
description: "Usar cuando el build Docker falla por errores de certificado SSL, o cuando necesitás entender por qué el Dockerfile tiene SSL deshabilitado y cuándo debe corregirse."
estado: vigente
---

# SSL corporativo en build

## Qué es

El Dockerfile de COELSA.Intelligent tiene la verificación SSL deshabilitada en los pasos de instalación de dependencias:

```dockerfile
ENV NODE_TLS_REJECT_UNAUTHORIZED=0
ENV npm_config_strict_ssl=false
ENV PIP_TRUSTED_HOST="download.pytorch.org download-r2.pytorch.org pypi.org files.pythonhosted.org"
```

## Por qué está deshabilitado

El entorno de CI/CD de COELSA tiene un **proxy corporativo** que intercepta el tráfico HTTPS y lo re-encripta con sus propios certificados TLS. Estos certificados son de la CA corporativa de COELSA, que **no está instalada en las imágenes base** de Docker usadas en el pipeline.

Resultado: `npm` y `pip` ven certificados que no reconocen → error de SSL → fallo del build.

La deshabilitación de SSL es el workaround temporal mientras se resuelve la instalación de los CAs corporativos a nivel de imagen base.

## El riesgo

Con SSL deshabilitado, `npm` y `pip` **no verifican la autenticidad del servidor** durante la descarga de dependencias. Un atacante con posición de man-in-the-middle en la red corporativa podría inyectar paquetes maliciosos.

Este es un **riesgo aceptado** documentado en [[Riesgos de seguridad aceptados]].

## La solución correcta

1. Instalar los certificados CA corporativos en la imagen base de Docker
2. Eliminar las variables `NODE_TLS_REJECT_UNAUTHORIZED`, `npm_config_strict_ssl` y `PIP_TRUSTED_HOST` del Dockerfile

Esta solución requiere coordinación con el equipo de infraestructura de COELSA.

## Relacionado

- [[Dockerfile]] — El archivo donde viven estas variables
- [[Riesgos de seguridad aceptados]] — El riesgo 3 (SSL en build)
- [[Pipelines Azure DevOps]] — El entorno de CI/CD donde aplica
- [[MOC - CI-CD y Despliegue]] — Índice del cluster de CI/CD
