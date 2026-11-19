"""Comandos públicos del ciclo de regresión."""

from comparison import compare
from model_quality import score_models
from promotion import promote
from release import gate, replay
from retest import verify_fix


def register_commands(sub):
    for name in ("validate", "run"):
        parser = sub.add_parser(name, help="Validar o ejecutar el catálogo versionado")
        parser.add_argument("--suite", required=True)
        parser.add_argument("--profile")
        parser.add_argument("--corpus")
        if name == "run":
            parser.add_argument("--env", required=True)
            parser.add_argument("--build", required=True)
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
    parser.add_argument("--out", required=True)
    parser.set_defaults(workflow_handler=promote)
    parser = sub.add_parser(
        "score-models", help="Medir detección en versiones con fallos conocidos"
    )
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--out", required=True)
    parser.set_defaults(workflow_handler=score_models)
