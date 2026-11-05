#!/usr/bin/env python3
"""Exporta casos revisados a CSV de Azure y registro CSV de resultados declarados."""
import argparse
import csv
import json
from pathlib import Path
import sys

HEADERS = ['ID', 'Work Item Type', 'Title', 'Test Step', 'Step Action', 'Step Expected', 'Area Path', 'Assigned To', 'State']


def cell(value):
    value = str(value)
    # Evitar fórmulas al abrir el CSV en planillas; conservar contenido en JSON de trazabilidad.
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registry', required=True); p.add_argument('--out', required=True)
    p.add_argument('--area'); p.add_argument('--assigned-to'); p.add_argument('--state')
    p.add_argument('--release', required=True); p.add_argument('--results', help='JSON opcional: ID -> resultado'); p.add_argument('--executed', help='JSON opcional: ID -> prueba ejecutada'); p.add_argument('--evidence', help='JSON opcional: ID -> evidencia')
    args = p.parse_args()
    try:
        data = json.loads(Path(args.registry).read_text(encoding='utf-8'))
        if data.get('schema') != 'qa-regression/1' or not isinstance(data.get('cases'), list) or not data['cases']:
            raise ValueError('Registro vacío o inválido')
        if not args.release.strip(): raise ValueError('Release obligatoria')
        azure_values = (args.area, args.assigned_to, args.state)
        if any(x is not None for x in azure_values) and not all(x and x.strip() for x in azure_values):
            raise ValueError('Para Azure indicar área, asignado y estado')
        def load_map(path):
            value = json.loads(Path(path).read_text(encoding='utf-8')) if path else {}
            if not isinstance(value, dict) or any(not isinstance(v, str) or not v.strip() for v in value.values()):
                raise ValueError('Los datos por caso deben ser un objeto de textos no vacíos')
            return value
        results, executed, evidence = load_map(args.results), load_map(args.executed), load_map(args.evidence)
        cases = data['cases']; ids = {c['id'] for c in cases}
        if len(ids) != len(cases) or not all(set(mapping) <= ids for mapping in (results, executed, evidence)): raise ValueError('IDs duplicados o resultados para casos desconocidos')
        titles = [f"[{c['id']}] {c['title']}" for c in cases]
        if all(azure_values) and (len(set(titles)) != len(titles) or any(len(t) > 128 for t in titles)): raise ValueError('Título repetido o mayor a 128 caracteres con ID incluido')
        out = Path(args.out); out.mkdir(mode=0o700, parents=False, exist_ok=False)
        if all(azure_values):
            with (out / 'azure-test-cases.csv').open('x', encoding='utf-8-sig', newline='') as f:
                w = csv.writer(f); w.writerow(HEADERS)
                for case, title in zip(cases, titles):
                    for i, step in enumerate(case['steps'], 1):
                        w.writerow([cell(x) for x in ['', 'Test Case', title, i, step,
                                    case['expected'] if i == len(case['steps']) else '', args.area, args.assigned_to, args.state]])
        with (out / 'registro-pruebas.csv').open('x', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f); w.writerow(['Release', 'Aplicación', 'Funcionalidad', 'ID local', 'Caso', 'Prueba prevista', 'Qué se ejecutó', 'Resultado', 'Evidencia'])
            for c in cases:
                w.writerow([cell(x) for x in [args.release, data['application'], c['feature'], c['id'], c['title'], '; '.join(c['steps']) + ' → ' + c['expected'], executed.get(c['id'], 'Sin evidencia de ejecución individual'), results.get(c['id'], 'Sin resultado individual'), evidence.get(c['id'], 'No informada')]])
        (out / 'trazabilidad.json').write_text(json.dumps({'schema':'qa-export-trace/1', 'release':args.release,
             'notice':'IDs locales están en los títulos; IDs de Azure vacíos crean casos nuevos. No se importó nada.',
             'cases':[{**c, 'azure_title':t} for c,t in zip(cases,titles)]}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(f'Exportación preparada: {out}')
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'Error: {exc}', file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
