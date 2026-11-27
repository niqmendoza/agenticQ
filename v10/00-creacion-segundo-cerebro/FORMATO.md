# Segundo cerebro en Open Knowledge Format

El bundle se publica en OKF 0.2, la versión del repositorio de Google Cloud Platform que se tomó como referencia. Cada concepto ocupa un Markdown con frontmatter YAML y un campo `type`. Los índices permiten recorrer el contenido por niveles y los enlaces Markdown representan las relaciones. [Especificación OKF 0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)

## Archivos de trabajo y entrega

| Capa | Archivos | Uso |
|---|---|---|
| Mapa local | `mapa.json`, `indice.sqlite`, `borradores/` | Inventario del commit, búsquedas de código redactado y ficha inicial por módulo. |
| Contexto de Copilot | `contexto.json` por consulta | Mapa paginado, resultados breves o rangos exactos; incluye el commit y el límite de caracteres. |
| Bundle OKF | `corpus/index.md`, `corpus/aplicacion.md`, `corpus/temas/` y `corpus/mocs/` | Índices temáticos, conceptos tipados, mapas de contenido, fuentes y relaciones. |
| Control de entrega | `manifiesto.json`, `fichas.json`, `taxonomia.json` y `entrega.json` | Cobertura, insumos para republicar y recibo de integridad. |

```text
corpus/
├── index.md
├── aplicacion.md
├── temas/
│   ├── consultas/
│   │   ├── index.md
│   │   └── concepto-consulta-estado.md
│   └── trazabilidad/
│       ├── index.md
│       └── concepto-referencia-tramite.md
└── mocs/
    └── respuesta-tramites.md
```

El índice raíz declara `okf_version: "0.2"`. Cada concepto de la aplicación registra citas en `sources` y las vincula con la afirmación mediante notas al pie. Las fuentes identifican el commit Git, el archivo y las líneas citadas. Los conceptos redactados a partir de fichas se publican con `status: draft` y con las referencias comprobadas estructuralmente. La clasificación de los conceptos, como `Regla funcional` o `Interfaz`, pertenece al dominio de QA. [Conceptos, fuentes y enlaces en OKF 0.2](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md#4-concept-documents)

El inventario toma archivos rastreados de un commit Git local. Registra omisiones por formato, tamaño y otras causas. Excluye, entre otros, archivos de credenciales, dependencias o generados conocidos, binarios, enlaces y submódulos. El límite por archivo se ajusta con `--max-kib-archivo`. La redacción de patrones sensibles es heurística. El índice de código y los contextos de búsqueda quedan en el área de trabajo de la etapa 00. La etapa 01 indexa solo `corpus/` y conserva las rutas originales de los conceptos.

## Ficha técnica y taxonomía de producto

Cada nota explica un concepto. El módulo de la ficha identifica el grupo técnico que mantiene sus fuentes. `taxonomia.json` define la navegación por áreas del producto y los MOCs. Dos conceptos del mismo módulo pueden pertenecer a áreas distintas. [Ejemplo de ficha](ejemplos/ficha.demo.json) · [Ejemplo de taxonomía](ejemplos/taxonomia.demo.json)

```json
{
  "modulo": "api",
  "hechos": [
    {
      "id": "consulta-estado",
      "tipo": "regla",
      "titulo": "Estado de un trámite conocido",
      "descripcion": "Explica qué estado devuelve la consulta del trámite de demostración.",
      "estado": "vigente",
      "afirmacion": "El trámite sintético QA-17 está en revisión y la respuesta cita REG-17.",
      "evidencia": [
        {"archivo": "api/tramites.py", "desde": 2, "hasta": 2, "localizador": "REG-17"}
      ],
      "relaciones": [
        {"tipo": "usa", "destino": "api/referencia-tramite", "motivo": "La referencia acompaña al estado devuelto."}
      ]
    }
  ],
  "pendientes": []
}
```

`tipo` admite `flujo`, `regla`, `interfaz`, `dato`, `prueba` y `operacion`. Usá IDs estables y únicos en cada área. `estado` admite `vigente`, `planificado`, `historico` y `por-confirmar`. El estado describe el conocimiento documentado. Cada hecho admite hasta 600 caracteres y una a tres citas a rangos de hasta 40 líneas. El localizador es texto literal del rango redactado, sin distinción de mayúsculas. La validación comprueba que la referencia existe en el commit. La revisión de QA confirma que la referencia respalda la afirmación y el estado.

Cada relación temática requiere `tipo`, `destino` y `motivo`. Elegí un verbo específico como `depende de`, `usa`, `limita`, `implementa`, `autoriza` o `valida`. Cada nota requiere una relación entrante o saliente y el publicador genera enlaces de regreso. Los MOCs enlazan al menos dos conceptos y explican el propósito de cada vínculo. El índice raíz lista cada concepto exactamente una vez, con la descripción de su ficha.

`publicar.py` requiere `--taxonomia RUTA` para este flujo. Si hay incumplimientos, `validacion-grafo.json` registra las incidencias y la publicación devuelve código 2. El código 3 conserva una entrega con pendientes de cobertura. `diagnosticar.py` vuelve a comprobar el índice raíz, la estructura de los MOCs, los enlaces y las notas aisladas antes de probar la recuperación. El modo explícito `--por-modulo` permite reconstruir entregas anteriores y el diagnóstico lo identifica por separado. La etapa 01 admite ambos formatos.

## Agrupación y actualización

Sin configuración se asigna un módulo por directorio de primer nivel y `raiz` para archivos sueltos. Para repositorios grandes, configurá prefijos de módulos funcionales y dependencias entre ellos. El prefijo más específico gana si hay solapamiento.

```json
{
  "api": {"prefijos": ["servicios/api"]},
  "web": {"prefijos": ["apps/frontend"], "depende_de": ["api"]}
}
```

`mapear.py --anterior` marca fichas reutilizables. `publicar.py --anterior` las incorpora si coinciden la configuración, las huellas del módulo y la raíz, y los objetos citados. Un cambio en una dependencia declarada marca su módulo consumidor para revisión. En los repositorios con módulos compartidos, reflejá esas dependencias en la configuración o pasá una ficha nueva para los módulos afectados.

## Bóveda de trabajo

`exportar_vault.py` publica una copia Markdown del corpus en una carpeta nueva. Si se indican notas preexistentes, la copia incluye sus enlaces bajo «Notas preexistentes». La entrega con recibo se conserva como entrada para la etapa 01.

```sh
python v10/00-creacion-segundo-cerebro/scripts/exportar_vault.py --cerebro "ENTREGA_CEREBRO" --destino "segund_cerebro/coelsa-intelligent-brain" --referencia "Bóveda anterior" "RUTA_A_NOTA_DE_ENTRADA.md"
```

## Consumo

El contexto se limita sobre el JSON completo. Una búsqueda puede reunir hasta diez consultas y alterna resultados entre ellas. Para el análisis de QA se usan los extractos del corpus, con el presupuesto de la etapa 01. `diagnosticar.py` evalúa el bundle con ese recuperador y reúne los tamaños de contexto, los resultados de las consultas y los cortes registrados de Copilot. Usa PyYAML, incluido en las dependencias de V10. Una comparación de tokens requiere cortes nativos de dos corridas sobre el mismo alcance, commit y modelo. [Medición y diagnóstico](MEDICION.md)

Para una publicación V3, el perfil de aplicación y las fichas QC agregan `corpus/inicio.md` y `corpus/qc/`. [Formato de escenarios V3](V3-QC.md)
