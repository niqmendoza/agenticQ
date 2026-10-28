---
title: "Riesgos de seguridad aceptados"
type: referencia
tags: [coelsa-intelligent, seguridad, riesgos, aceptados, csp]
aliases: [Accepted risks, Riesgos aceptados COELSA, Security risks]
description: "Usar cuando necesitás conocer qué vulnerabilidades de seguridad están conscientemente aceptadas en COELSA.Intelligent y por qué no se resuelven."
estado: vigente
---

# Riesgos de seguridad aceptados

## Qué es

No todos los riesgos de seguridad son solucionables sin un costo de ingeniería desproporcionado o sin romper funcionalidades críticas. COELSA.Intelligent tiene **3 riesgos aceptados documentados** con su justificación.

## Riesgos aceptados

### 1. `CSP: style-src unsafe-inline` (MEDIUM)

**Descripción**: Los atributos `style=""` inline no pueden recibir nonces. El header CSP incluye `style-src 'unsafe-inline'`.

**Por qué se acepta**: Eliminar todos los atributos `style=""` inline requeriría refactorizar toda la capa de componentes del upstream (miles de líneas). El riesgo de estilo es considerablemente menor que el de script.

**Condición de reapertura**: si se encuentra un vector de ataque CSS injection específico en la app.

---

### 2. `CSP: script-src unsafe-eval` (MEDIUM)

**Descripción**: `unsafe-eval` está en `script-src`. El header lo incluye.

**Por qué se acepta**: Mermaid (diagramas) y el sistema de artifacts requieren `eval()`. Desactivar `unsafe-eval` rompe estas funcionalidades sin un workaround disponible actualmente.

**Condición de reapertura**: si se encuentra una versión de Mermaid que no requiere `eval()`.

---

### 3. SSL deshabilitado en build Docker

**Descripción**: El Dockerfile tiene `NODE_TLS_REJECT_UNAUTHORIZED=0` y `PIP_TRUSTED_HOST`.

**Por qué se acepta**: Necesario en el entorno de CI/CD de COELSA donde el proxy corporativo intercepta HTTPS con certificados no instalados en la imagen base. La solución correcta es instalar los CAs corporativos en la imagen, lo que requiere coordinación con infraestructura.

**Ver**: [[SSL corporativo en build]]

---

## Relacionado

- [[CSP con nonces]] — Los riesgos 1 y 2 son parte del estado CSP
- [[SSL corporativo en build]] — El detalle del riesgo 3
- [[MOC - Seguridad]] — Índice del cluster de seguridad
