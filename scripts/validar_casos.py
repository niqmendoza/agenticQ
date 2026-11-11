#!/usr/bin/env python3
"""Verifica citas literales de borradores contra fragmentos recuperados, no su significado."""
import argparse
import json
from pathlib import Path
import re
import sys


def validate(context, cases):
    if not isinstance(context, dict) or not isinstance(context.get('sources'), dict) or not isinstance(context.get('passages'), list):
        raise ValueError('Contexto sin fuentes o fragmentos válidos')
    rag = context.get('schema') == 'qa-context/1'
    if rag:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'historico' / 'Post Harness V2' / 'scripts'))
        from verify_context import verify
        verify(context)
    elif not (context.get('version') == '2.0.0' and context.get('revision') and context.get('line_format')):
        raise ValueError('Formato de contexto no reconocido')
    passages = []
    for p in context['passages']:
        if not isinstance(p, dict) or p.get('source') not in context['sources'] or not isinstance(p.get('text'), str):
            raise ValueError('Fragmento inválido')
        text = p['text']
        if not rag:
            lines = text.splitlines()
            if not lines or any(re.match(r'^\d+\|', line) is None for line in lines):
                raise ValueError('Fragmento local sin líneas numeradas')
            text = '\n'.join(line.split('|', 1)[1] for line in lines)
        passages.append((p['source'], p.get('id'), text))
    if not isinstance(cases, dict) or cases.get('schema') != 'qa-cases/1' or not isinstance(cases.get('cases'), list) or not cases['cases']:
        raise ValueError('Se requiere qa-cases/1 con al menos un caso')
    errors = []
    ids = set()
    for i, case in enumerate(cases['cases'], 1):
        if not isinstance(case, dict):
            errors.append(f'Caso {i}: formato inválido'); continue
        ident = case.get('id')
        if not isinstance(ident, str) or not ident.strip() or ident in ids:
            errors.append(f'Caso {i}: ID vacío o duplicado')
        else:
            ids.add(ident)
        if any(not isinstance(case.get(k), str) or not case[k].strip() for k in ('title', 'expected')):
            errors.append(f'Caso {i}: título o esperado vacío')
        if not isinstance(case.get('steps'), list) or not case['steps'] or any(not isinstance(x, str) or not x.strip() for x in case['steps']):
            errors.append(f'Caso {i}: pasos inválidos')
        refs = case.get('references')
        if not isinstance(refs, list) or not refs:
            errors.append(f'Caso {i}: faltan referencias'); continue
        for ref in refs:
            if not isinstance(ref, dict) or not isinstance(ref.get('quote'), str) or not ref['quote'].strip():
                errors.append(f'Caso {i}: cita vacía o inválida'); continue
            source, pid, quote = ref.get('source'), ref.get('passage_id'), ref['quote']
            if rag and (not isinstance(pid, str) or not pid):
                errors.append(f'Caso {i}: falta ID de fragmento RAGFlow'); continue
            if not any(source == sid and (not rag or pid == passage_id) and quote in text for sid, passage_id, text in passages):
                errors.append(f'Caso {i}: cita o referencia no encontrada en el contexto')
    return {'schema': 'qa-case-validation/1', 'valid': not errors, 'cases_checked': len(cases['cases']),
            'context_integrity': 'verified_ragflow' if rag else 'not_verified_local_packet', 'errors': errors,
            'semantic_validation': 'not_performed', 'human_review': 'required'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context', required=True); parser.add_argument('--cases', required=True); parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        with open(args.context, encoding='utf-8') as f: context = json.load(f)
        with open(args.cases, encoding='utf-8') as f: cases = json.load(f)
        result = validate(context, cases)
        with open(args.out, 'x', encoding='utf-8') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'No se pudo validar: {type(exc).__name__}: {exc}', file=sys.stderr); return 2
    print('Citas válidas' if result['valid'] else 'Citas inválidas; revisar informe')
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    sys.exit(main())
