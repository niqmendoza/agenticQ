# Segundo cerebro en Open Knowledge Format

El bundle se publica en OKF 0.2, la versión del repositorio de Google Cloud Platform que se tomó como referencia. Cada concepto ocupa un Markdown con frontmatter YAML y un campo `type`. Los índices permiten recorrer el contenido por niveles y los enlaces Markdown representan las relaciones. [Especificación OKF 0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)

## Archivos de trabajo y entrega

| Capa | Archivos | Uso |
|---|---|---|
| Mapa local | `mapa.json`, `indice.sqlite`, `borradores/` | Inventario del commit, búsquedas de código redactado y ficha inicial por módulo. |
| Contexto de Copilot | `contexto.json` por consulta | Mapa paginado, resultados breves o rangos exactos; incluye el commit y el límite de caracteres. |
| Bundle OKF | `corpus/index.md`, `corpus/aplicacion.md`, `corpus/modulos/` | Índices, conceptos tipados, fuentes y relaciones. |
| Control de entrega | `manifiesto.json`, `fichas.json`, `entrega.json` | Cobertura por módulo, insumos para republicar y recibo de integridad. |

```text
corpus/
├── index.md
├── aplicacion.md
└── modulos/
    ├── index.md
    └── api/
        ├── index.md
        ├── modulo.md
        └── concepto-consulta-estado.md
```

El índice raíz declara `okf_version: "0.2"`. Cada concepto de la aplicación registra citas en `sources` y las vincula con la afirmación mediante notas al pie. Las fuentes identifican el commit Git, el archivo y las líneas citadas. Los conceptos redactados a partir de fichas se publican con `status: draft` y con las referencias comprobadas estructuralmente. La clasificación de los conceptos, como `Regla funcional` o `Interfaz`, pertenece al dominio de QA. [Conceptos, fuentes y enlaces en OKF 0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md#4-concept-documents)

El inventario toma archivos rastreados de un commit Git local. Registra omisiones por formato, tamaño y otras causas. Excluye, entre otros, archivos de credenciales, dependencias o generados conocidos, binarios, enlaces y submódulos. El límite por archivo se ajusta con `--max-kib-archivo`. La redacción de patrones sensibles es heurística. El índice de código y los contextos de búsqueda quedan en el área de trabajo de la etapa 00. La etapa 01 indexa solo `corpus/` y conserva las rutas originales de los conceptos.

## Ficha por módulo

```json
{
  "modulo": "api",
  "hechos": [
    {
      "id": "consulta-estado",
      "tipo": "regla",
      "titulo": "Estado de un trámite conocido",
      "afirmacion": "El trámite sintético QA-17 está en revisión y la respuesta cita REG-17.",
      "evidencia": [
        {"archivo": "api/tramites.py", "desde": 2, "hasta": 2, "localizador": "REG-17"}
      ]
    }
  ],
  "pendientes": []
}
```

`tipo` admite `flujo`, `regla`, `interfaz`, `dato`, `prueba` y `operacion`. Usá IDs estables. Cada hecho admite hasta 600 caracteres y una a tres citas a rangos de hasta 40 líneas. El localizador es texto literal del rango redactado, sin distinción de mayúsculas. La validación comprueba que la referencia existe en el commit. La revisión de QA confirma que esa referencia respalda la afirmación.

Cada hecho puede incluir `"relaciones": [{"tipo": "usa", "destino": "api/consulta-estado"}]`. Los tipos disponibles son `depende de`, `usa`, `valida`, `documenta` y `relacionado con`. La publicación traduce estos vínculos a enlaces al concepto destino. Si el concepto destino está pendiente, el vínculo queda en `relaciones_pendientes` del manifiesto. Las dependencias declaradas entre módulos también se publican como enlaces.

El estado por módulo indica si la ficha se revisó, se reutilizó o quedó pendiente. El manifiesto registra las cantidades de hechos y pendientes. La publicación devuelve código 3 si hay pendientes o todavía falta publicar un hecho. La etapa 01 admite una entrega con cobertura parcial y al menos un hecho, y registra su procedencia y versión OKF.

## Agrupación y actualización

Sin configuración se asigna un módulo por directorio de primer nivel y `raiz` para archivos sueltos. Para repositorios grandes, configurá prefijos de módulos funcionales y dependencias entre ellos. El prefijo más específico gana si hay solapamiento.

```json
{
  "api": {"prefijos": ["servicios/api"]},
  "web": {"prefijos": ["apps/frontend"], "depende_de": ["api"]}
}
```

`mapear.py --anterior` marca fichas reutilizables. `publicar.py --anterior` las incorpora si coinciden la configuración, las huellas del módulo y la raíz, y los objetos citados. Un cambio en una dependencia declarada marca su módulo consumidor para revisión. En los repositorios con módulos compartidos, reflejá esas dependencias en la configuración o pasá una ficha nueva para los módulos afectados.

## Consumo

El contexto se limita sobre el JSON completo. Una búsqueda puede reunir hasta diez consultas y alterna resultados entre ellas. Para el análisis de QA se usan los extractos del corpus, con el presupuesto de la etapa 01. `diagnosticar.py` evalúa el bundle con ese recuperador y reúne los tamaños de contexto, los resultados de las consultas y los cortes registrados de Copilot. Usa PyYAML, incluido en las dependencias de V10. Una comparación de tokens requiere cortes nativos de dos corridas sobre el mismo alcance, commit y modelo. [Medición y diagnóstico](MEDICION.md)
