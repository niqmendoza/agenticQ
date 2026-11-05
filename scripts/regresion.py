#!/usr/bin/env python3
"""Registra casos revisados y prepara planes de regresión por release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from validar_casos import validate


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_new(path, data):
    with open(path, 'x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2); f.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('init'); init.add_argument('--registry', required=True); init.add_argument('--application', required=True)
    add = sub.add_parser('add'); add.add_argument('--registry', required=True); add.add_argument('--context', required=True); add.add_argument('--cases', required=True); add.add_argument('--feature', required=True); add.add_argument('--tests', required=True, help='Ruta o identificador de pruebas en el proyecto de aplicación'); add.add_argument('--reviewed', action='store_true', required=True, help='Confirma revisión humana de los casos')
    plan = sub.add_parser('plan'); plan.add_argument('--registry', required=True); plan.add_argument('--release', required=True); plan.add_argument('--feature', help='Funcionalidad nueva confirmada por el usuario'); plan.add_argument('--changed-rules', action='store_true'); plan.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        registry = Path(args.registry)
        if args.action == 'init':
            if not args.application.strip(): raise ValueError('Nombre de aplicación vacío')
            write_new(registry, {'schema': 'qa-regression/1', 'application': args.application, 'cases': []})
        else:
            data = read(registry)
            if data.get('schema') != 'qa-regression/1' or not isinstance(data.get('cases'), list): raise ValueError('Registro inválido')
            if args.action == 'add':
                if not args.feature.strip() or not args.tests.strip(): raise ValueError('Funcionalidad y pruebas son obligatorias')
                context, cases = read(args.context), read(args.cases)
                result = validate(context, cases)
                if not result['valid']: raise ValueError('Las referencias no superaron la validación')
                ids = {case['id'] for case in data['cases']}
                if any(case['id'] in ids for case in cases['cases']): raise ValueError('ID ya registrado; revisar cambio sin sobreescribir')
                sha = hashlib.sha256(Path(args.context).read_bytes()).hexdigest()
                for case in cases['cases']:
                    data['cases'].append({**case, 'feature': args.feature, 'tests': args.tests, 'context_sha256': sha, 'review': 'human_confirmed'})
                # Reemplazo atómico; usar un solo editor por registro.
                temp = None
                try:
                    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=registry.parent, delete=False) as f:
                        temp = f.name; json.dump(data, f, ensure_ascii=False, indent=2); f.write('\n')
                    os.replace(temp, registry); temp = None
                finally:
                    if temp is not None: os.unlink(temp)
            else:
                if not args.release.strip(): raise ValueError('Release vacía')
                changed = args.changed_rules
                write_new(args.out, {'schema': 'qa-release-plan/1', 'application': data['application'], 'release': args.release,
                    'regression_case_ids': [c['id'] for c in data['cases']],
                    'test_targets': sorted({c['tests'] for c in data['cases']}),
                    'new_feature': args.feature if args.feature else None,
                    'new_feature_status': 'consultar_y_validar_solo_esta_funcionalidad' if args.feature else 'preguntar_si_hay_funcionalidad_nueva',
                    'existing_rules_status': 'revision_requerida' if changed else 'vigencia_no_verificada',
                    'execution_status': 'pendiente',
                    'notice': 'Ejecutar regresión completa con el comando real; un plan no ejecuta ni prueba cobertura.'})
        print('Operación completada')
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'Error: {exc}', file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
