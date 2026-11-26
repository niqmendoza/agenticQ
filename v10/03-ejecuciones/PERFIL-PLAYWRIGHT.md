# Contrato Playwright de V10

Declarale al perfil los controles y rutas reales de la aplicación de QA. El diseño usa esos nombres en sus pasos y criterios. Este ejemplo supone un login local que responde al navegador y abre el chat.

## Sesión compartida

Agregá una entrada a `browser_setups` por actor. La ruta inicial y las navegaciones deben estar en `browser_paths`. El método y la ruta HTTP del login también van en `http_operations`.

```json
{
  "browser_setups": {
    "qa_chat": {
      "actor": "lector_qa",
      "browser_path": "/login",
      "timeout_seconds": 8,
      "browser_steps": [
        {"id": "usuario", "type": "fill", "control": "login_user", "value_env": "CHAT_USUARIO"},
        {"id": "clave", "type": "fill", "control": "login_password", "value_env": "CHAT_PASSWORD"},
        {"id": "entrar", "type": "click", "control": "login_submit"}
      ],
      "login": {"step": "entrar", "method": "POST", "path": "/api/session"},
      "ready_control": "composer"
    }
  }
}
```

Para un caso que use esa sesión, declarale `"browser_setup": "qa_chat"` y la ruta de la pantalla comprobada en `browser_path`. El runner autentica y comprueba el control de disponibilidad una vez. Después crea por caso un contexto separado con cookies y almacenamiento del actor en memoria. Si el producto conserva conversaciones, archivos o preferencias del lado servidor, diseñá escenarios con datos propios y definí su limpieza en QA.

Podés sumar `probe` con `browser_steps` y `criteria` a la sesión. Se ejecuta después de ver el control listo. Verificá el modelo exacto de QA y un resultado breve con `control_contains` o `control_text`. Elegí una acción que pueda correr una vez por sesión y que use datos sintéticos. Los casos de login o logout van con `"browser_session": "fresh"`, sus propios pasos y, cuando corresponde, `browser_login` con el mismo contrato de método, ruta y click. En ese campo podés declarar `status` para una respuesta negativa esperada y comprobar también su mensaje en la UI.

El runner observa el método, ruta y estado HTTP del login. Para `401`, `403` y `429` publica causas distintas. Una respuesta exitosa seguida de un control ausente también tiene su propio motivo. El navegador bloquea redirecciones HTTP del flujo automatizado y navegaciones fuera del perfil. Si el inicio necesita un IdP externo o un mecanismo interactivo diferente, revisá con QA la modalidad de acceso para ese entorno y registrá la capacidad pendiente en el diseño si corresponde.

## Modelo y resultado nuevo

```json
{
  "browser_setup": "qa_chat",
  "browser_model": {"value": "modelo-qa", "before": "enviar"},
  "browser_preconditions": [{"control": "estado_adjuntos", "equals": "Deshabilitados"}],
  "browser_steps": [
    {"id": "seleccionar", "type": "select", "control": "modelo", "value": "modelo-qa"},
    {"id": "verificar", "type": "verify_model", "control": "modelo", "property": "value", "value": "modelo-qa"},
    {"id": "previos", "type": "capture_count", "control": "turno_asistente"},
    {"id": "pregunta", "type": "fill", "control": "composer", "value": "Consultá el trámite sintético QA-17."},
    {"id": "enviar", "type": "click", "control": "submit"},
    {"id": "fin", "type": "wait_visible", "control": "turno_completo", "scope": "previos"}
  ],
  "criteria": [
    {"id": "respuesta", "expected": "El mensaje nuevo contiene QA-17", "check": {
      "type": "control_contains", "control": "texto_turno", "scope": "previos", "equals": "QA-17"
    }},
    {"id": "sin-enlace", "expected": "El mensaje nuevo carece de adjunto", "check": {
      "type": "control_absent", "control": "enlace_turno", "scope": "previos"
    }}
  ]
}
```

Usá `property: text` para un selector con etiqueta visible o `property: value` para un valor exacto de formulario. El valor declarado en `browser_model` debe verificarse antes de `before`. El selector `turno_asistente` debe ubicar solo los mensajes del asistente, en el orden en que se agregan. El scope usa el índice del primer turno agregado después de la captura. En un chat que virtualiza o reemplaza los turnos, diseñá el caso contra un control con identidad verificable y documentá esa capacidad del producto. El estado en `browser_preconditions` se observa al abrir la pantalla. Si el indicador falta o difiere, el caso queda bloqueado y la evidencia identifica el control. `control_absent` con scope exige que exista primero el turno nuevo.

## Adjuntos y descargas

Hacé un caso distinto por formato y variante de comportamiento. Recordá citar el criterio para el límite permitido y excedido. Agregá una variante con `grupo`, `formato` y `tipo`. Para `limite_permitido` y `limite_excedido` el validador requiere un adjunto y una aserción de texto específica. Para `descarga` exige una comprobación de contenido del formato declarado.

```json
{
  "variante": {"grupo": "exportacion", "formato": "md", "tipo": "descarga"},
  "browser_steps": [{"id": "exportar", "type": "download", "control": "boton_exportar"}],
  "criteria": [{
    "id": "contenido", "expected": "La descarga contiene el trámite QA-17",
    "check": {"type": "download_file", "step": "exportar", "extension": ".md", "min_bytes": 20, "contains": ["QA-17"]}
  }]
}
```

`contains` admite valores literales en texto UTF-8 y XML interno de DOCX y XLSX. El lector consulta la hoja 1 de XLSX y las cadenas compartidas cuando existen. En la evidencia quedan la extensión, los bytes, el hash y cuántos valores coincidieron. Para otros formatos, el criterio básico de extensión y tamaño sigue disponible. Los fixtures PDF y XLSX se generan con `mockups.py` y se inspeccionan antes de publicar su recibo.
