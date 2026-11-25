"""Comandos públicos del ciclo de regresión."""

from comparison import compare
from model_quality import score_models
from promotion import promote
from release import gate, replay
from retest import verify_fix


def register_commands(sub):
    for name in ("validate", "run"):
        parser = sub.add_parser(name, help="Validar o ejecutar el catálogo versionado")
        selection = parser.add_mutually_exclusive_group(required=True)
        selection.add_argument("--suite")
        selection.add_argument("--app", help="ID de la aplicación en el repo de regresiones")
        parser.add_argument("--regressions", help="Ruta local al repo de regresiones")
        parser.add_argument("--new-suite", help="Casos nuevos para probar junto al catálogo")
        parser.add_argument("--profile")
        parser.add_argument("--corpus")
        parser.add_argument(
            "--chrome-visible",
            action="store_true",
            help="Usar el Chrome instalado con ventana",
        )
        if name == "run":
            parser.add_argument("--env", required=True)
            parser.add_argument("--build", required=True)
            parser.add_argument("--build-ref", help="Identificador verificable del build")
            parser.add_argument("--bloqueos-preflight", help="JSON de casos omitidos por el diagnóstico V9")
            parser.add_argument(
                "--id", help="ID nuevo, generado automáticamente si se omite"
            )
        parser.set_defaults(workflow_handler=replay)
    parser = sub.add_parser(
        "gate", help="Calcular dictamen de release y exportar JUnit"
    )
    parser.add_argument("--run", required=True)
    parser.set_defaults(workflow_handler=gate)
    parser = sub.add_parser("compare", help="Contrastar dos corridas o ZIP publicados")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    parser.set_defaults(workflow_handler=compare)
    parser = sub.add_parser(
        "verify-fix", help="Cerrar un hallazgo con una corrida de retest"
    )
    parser.add_argument("--run", required=True)
    parser.add_argument("--finding", required=True)
    parser.add_argument("--retest", required=True)
    parser.set_defaults(workflow_handler=verify_fix)
    parser = sub.add_parser(
        "promote", help="Copiar un plan y su manifiesto desde una corrida V5 o V6"
    )
    parser.add_argument("--from-run", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--app", required=True)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--out")
    destination.add_argument("--regressions", help="Incorporar al repo de regresiones")
    parser.add_argument("--case", action="append", help="ID aprobado para incorporar")
    parser.add_argument("--corpus", help="Fuentes para validar el catálogo")
    parser.add_argument("--profile", help="Perfil común para validar el catálogo")
    parser.add_argument("--openapi", help="Contrato de los casos seleccionados")
    parser.set_defaults(workflow_handler=promote)
    parser = sub.add_parser(
        "score-models", help="Medir detección en versiones con fallos conocidos"
    )
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--out", required=True)
    parser.set_defaults(workflow_handler=score_models)
