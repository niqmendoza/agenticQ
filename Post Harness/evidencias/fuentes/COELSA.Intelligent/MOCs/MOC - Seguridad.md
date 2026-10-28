---
title: "MOC — Seguridad"
type: moc
tags: [coelsa-intelligent, seguridad, owasp, csp, moc]
aliases: [MOC Seguridad, Hardening COELSA, Security COELSA]
description: "Usar cuando necesitás entender el estado de seguridad de COELSA.Intelligent: qué fue remediado, qué está aceptado como riesgo y qué dependencias tienen CVEs."
estado: vigente
---

# MOC — Seguridad

Las remediaciones de seguridad cubren OWASP Top 10: CSP, ReDoS, SSRF, Path Traversal y dependencias vulnerables. El scan de referencia es OWASP ZAP sobre OpenShift DEV (Febrero 2026).

## Notas de este cluster

### Remediaciones implementadas
- [[CSP con nonces]] — `NonceInjectionMiddleware`; diferencia entre dev (unsafe-inline) y OpenShift (nonces)
- [[Hardening ReDoS]] — 11 expresiones regulares convertidas a bounded quantifiers
- [[Protección SSRF]] — 9 endpoints con validación de URLs outbound; rechazo de IPs privadas y loopback
- [[Path Traversal]] — 8 endpoints con sanitización de paths de entrada de usuario

### Dependencias
- [[Dependencias vulnerables]] — jspdf, tar y sus overrides en `package.json`; política de actualización
- [[CVE-2025-7969 markdown-it]] — Por qué es un falso positivo (SSR deshabilitado) y cómo está suprimido en SonarCloud

### Riesgos aceptados
- [[Riesgos de seguridad aceptados]] — `style-src unsafe-inline`, `script-src unsafe-eval`, SSL deshabilitado en build

## MOCs vecinos

- [[MOC - Arquitectura]] — SSR deshabilitado elimina el vector del CVE de markdown-it
- [[MOC - Autenticación y Permisos]] — bcrypt, JWT y Azure AD como primera línea de defensa
- [[MOC - CI-CD y Despliegue]] — El Dockerfile tiene SSL deshabilitado temporalmente; riesgo documentado
- [[MOC - Decisiones]] — Las decisiones de seguridad y sus justificaciones indexadas
