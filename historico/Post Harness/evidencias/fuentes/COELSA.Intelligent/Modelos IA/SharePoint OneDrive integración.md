---
title: "SharePoint OneDrive integración"
type: concepto
tags: [coelsa-intelligent, modelos-ia, sharepoint, onedrive, microsoft, file-picker]
aliases: [SharePoint integration, OneDrive COELSA, Microsoft File Picker]
description: "Usar cuando trabajás con la integración de SharePoint/OneDrive en el input de chat, o cuando necesitás configurar los permisos de Azure AD para el File Picker."
estado: vigente
---

# SharePoint OneDrive integración

## Qué es

COELSA.Intelligent permite a los usuarios seleccionar archivos corporativos directamente desde **SharePoint** o **OneDrive** usando el **Microsoft File Picker v8**, sin necesidad de descargar y volver a subir el archivo.

## Cómo funciona

1. El usuario hace clic en el ícono de SharePoint en el input de chat
2. Se abre el File Picker en un popup/iframe usando la identidad del usuario (OAuth delegado)
3. El usuario selecciona el archivo
4. El backend descarga el archivo usando el token de acceso del usuario con permisos `Files.Read.All`
5. El archivo se procesa como cualquier otro archivo subido (ver [[Flujo de subida de archivos]])

## Requisitos de configuración

### Azure AD

La App Registration debe tener el permiso **`Files.Read.All`** (delegado). Este permiso permite leer cualquier archivo del tenant al que el usuario tenga acceso.

```env
SHAREPOINT_CLIENT_ID=<azure-client-id>
# Usar el mismo tenant de OAUTH_CLIENT_ID o uno separado
```

### CSP

El Route de OpenShift debe incluir en `connect-src`:
- `login.microsoftonline.com` — para el flujo OAuth del File Picker
- `graph.microsoft.com` — para descargar el contenido del archivo

Ver `docs/OPENSHIFT-CONFIGMAP.yaml` para el ejemplo completo.

## Relacionado

- [[Azure AD OAuth]] — La App Registration que necesita el permiso Files.Read.All
- [[Flujo de subida de archivos]] — Lo que ocurre una vez seleccionado el archivo
- [[CSP con nonces]] — La CSP donde deben estar los dominios de Microsoft
- [[Despliegue en OpenShift]] — La configuración del Route donde vive la CSP
- [[MOC - Modelos IA y Routing]] — Índice del cluster de modelos
