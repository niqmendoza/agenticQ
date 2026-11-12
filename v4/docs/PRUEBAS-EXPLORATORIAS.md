# Recorridos variables y pruebas negativas

## Recorrer Swagger o una interfaz

Un caso con `browser_walk` mezcla las acciones de cada ronda con una semilla. Cada acción aparece una vez por ronda y todas se ejecutan en la misma sesión de navegador. Se permiten hasta ocho acciones por ronda y tres rondas. El caso comprueba sus invariantes al cargar la página y después de cada acción.

- `resize` cambia el tamaño de ventana con `width` y `height`.
- `scroll` desplaza una distancia acotada indicada en `pixels`.
- `reload` recarga la ruta del caso.
- `click` y `double_click` usan el nombre `control` de un selector declarado en `browser_controls` del perfil. Elegí controles de lectura como pestañas o paneles desplegables.

El runner conserva la página declarada para el recorrido y permite solicitudes HTTP GET/HEAD dentro del origen, más los scripts y hojas de estilo externos declarados en el perfil. Usá una instancia de pruebas. Los criterios disponibles incluyen `status`, `visible_text`, `walk_completed` (obligatorio) y `no_page_errors`. `visible_text` comprueba visibilidad según el localizador de Playwright. Si una acción falla o navega fuera de la página esperada, el recorrido queda incompleto y falla el criterio `walk_completed`. El JSON de evidencia guarda la semilla, el orden previsto, los pasos observados, sus tiempos, resultados y cantidad de excepciones de JavaScript sin capturar. [API de Playwright](https://playwright.dev/python/docs/api/class-page).

Ejemplo local sobre el Swagger de PAPPU, con el perfil y los casos ya registrados en la sesión:

```sh
python3 v4/src/qa.py execute --run "$RUN" --case PAPPU-SWAGGER-RECORRIDO --via playwright --seed 41
python3 v4/src/qa.py execute --run "$RUN" --case PAPPU-SWAGGER-RECORRIDO --via playwright --seed 73
```

Un manifiesto de `suite` también admite `seed` en entradas Playwright. Para reproducir una falla, usar la misma semilla, perfil, caso y versión de la aplicación. Comparar el orden previsto y el primer paso que dejó de cumplir un criterio. El informe por caso muestra el último intento y el historial conserva las demás semillas.

## Probar un tipo de entrada inválido

Partí de un fixture que ya pasó el camino válido. Cambiá un solo campo, conservá el resto y registrá un caso distinto para el rechazo. Si el contrato admite conversión de tipos, comprobá ese resultado en un caso separado. Definí el código HTTP y el error esperado a partir del contrato de cada API.

```sh
python3 v4/src/qa.py fixture-variant \
  --fixture v4/examples/validacion-tipos/valido.json \
  --path '["name"]' --value 7 --out "$RUN/name-entero.json"
python3 v4/src/qa.py execute --run "$RUN" --case TIPO-01 --via http --body "$RUN/name-entero.json"
```

El ejemplo `TIPO-01` está definido en [caso.json](../examples/validacion-tipos/caso.json) para una API de prueba con `POST /validate`, campo `name` de tipo string y rechazo 422. Registrá el caso y declará la operación en el perfil antes de ejecutar. El mismo comando permite variantes con `null`, booleanos, listas u objetos. `--path` admite claves e índices de array. El runner permite comprobar el tipo de un campo de respuesta con `json_type` y su valor con `json_equals`. Los fixtures se guardan con datos sintéticos y el runner conserva resultados de aserciones y metadatos en la evidencia.
