---
title: "Protección SSRF"
type: concepto
tags: [coelsa-intelligent, seguridad, ssrf, owasp, validacion]
aliases: [SSRF protection, Server-Side Request Forgery, Validación de URLs]
description: "Usar cuando necesitás agregar un endpoint que hace requests outbound a URLs de usuario, o cuando diagnosticás si un endpoint es vulnerable a SSRF."
estado: vigente
---

# Protección SSRF

## Qué es

**SSRF** (Server-Side Request Forgery) ocurre cuando un atacante puede hacer que el servidor haga requests a URLs arbitrarias, incluyendo servicios internos de la red (como metadata de cloud, servicios sin autenticación en la red interna, etc.).

COELSA.Intelligent aplicó validación de URLs outbound a **9 endpoints** que aceptan URLs de usuario.

## El fix

Antes de hacer cualquier request a una URL de input de usuario, se valida:

```python
from urllib.parse import urlparse
import ipaddress

def validate_url(url: str) -> bool:
    """
    Rechaza IPs privadas y loopback para prevenir SSRF.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    
    if not hostname:
        return False
    
    try:
        ip = ipaddress.ip_address(hostname)
        # Rechazar IPs privadas, loopback, link-local
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        # Es un hostname, no IP; permitir (puede haber restricciones adicionales)
        pass
    
    return True
```

## Qué se rechaza

- Loopback: `127.0.0.1`, `::1`, `localhost`
- Redes privadas: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- Link-local: `169.254.0.0/16` (metadata de cloud en AWS/GCP/Azure)
- Otros: `0.0.0.0`, rangos reservados

## Endpoints protegidos (9)

Los endpoints de importación de URLs (RAG de web), integración de herramientas externas, y cualquier endpoint que acepte una URL como input de usuario.

## Relacionado

- [[Hardening ReDoS]] — Otra remediación OWASP del mismo ciclo
- [[Path Traversal]] — Otra remediación del mismo ciclo
- [[MOC - Seguridad]] — Índice del cluster de seguridad
