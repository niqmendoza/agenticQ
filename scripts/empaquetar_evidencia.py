#!/usr/bin/env python3
"""Reúne únicamente archivos seleccionados y metadatos revisados; no anonimiza."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

STATES = {'ejecutado', 'no_ejecutado', 'bloqueado', 'no_aplica'}


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name} debe ser texto no vacío')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True, help='JSON con metadatos y artefactos revisados')
    p.add_argument('--base', required=True, help='Carpeta raíz de los archivos a copiar')
    p.add_argument('--out', required=True, help='Carpeta nueva de salida, fuera de base')
    p.add_argument('--reviewed', action='store_true', required=True, help='Se revisaron los datos para su transferencia')
    args = p.parse_args()
    try:
        base = Path(args.base).resolve(strict=True)
        out = Path(args.out).resolve()
        if not base.is_dir() or out == base or base in out.parents: raise ValueError('La salida debe estar fuera de la carpeta base')
        data = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('schema') != 'qa-evidence-input/1': raise ValueError('Esquema de entrada inválido')
        for key in ('application', 'release', 'scope', 'environment', 'versions', 'commands', 'sources', 'limitations', 'pending'):
            text(data.get(key), key)
        stages = data.get('stages')
        if not isinstance(stages, dict) or set(stages) != {'copilot', 'coelsa', 'azure'} or any(v not in STATES for v in stages.values()):
            raise ValueError('stages debe declarar copilot, coelsa y azure con estados permitidos')
        cases = data.get('cases')
        if not isinstance(cases, list): raise ValueError('cases debe ser una lista')
        ids = set()
        for case in cases:
            if not isinstance(case, dict): raise ValueError('Caso inválido')
            for key in ('id', 'feature', 'result', 'traceability', 'evidence'): text(case.get(key), f'caso.{key}')
            if case['id'] in ids: raise ValueError('ID de caso duplicado')
            ids.add(case['id'])
        artifacts = data.get('artifacts')
        if not isinstance(artifacts, list): raise ValueError('artifacts debe ser una lista')
        prepared = []
        for item in artifacts:
            if not isinstance(item, dict): raise ValueError('Artefacto inválido')
            text(item.get('path'), 'artifacts.path'); text(item.get('description'), 'artifacts.description')
            rel = Path(item['path'])
            if rel.is_absolute() or '..' in rel.parts: raise ValueError('Ruta de artefacto debe ser relativa y sin ..')
            current = base
            for part in rel.parts:
                current = current / part
                if current.is_symlink(): raise ValueError('No se aceptan enlaces simbólicos')
            source = current.resolve(strict=True)
            if base not in source.parents or not source.is_file(): raise ValueError('El artefacto debe ser un archivo dentro de base')
            prepared.append((source, item['description']))
        out.mkdir(mode=0o700, parents=False, exist_ok=False)
        target = out / 'artefactos'; target.mkdir(mode=0o700)
        exported = []
        for i, (source, description) in enumerate(prepared, 1):
            dest = target / f'{i:03d}-{source.name}'
            shutil.copyfile(source, dest)
            digest = hashlib.sha256()
            with dest.open('rb') as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b''): digest.update(chunk)
            exported.append({'path': f'artefactos/{dest.name}', 'description': description, 'sha256': digest.hexdigest(), 'bytes': dest.stat().st_size})
        package = {**data, 'schema': 'qa-evidence-package/1', 'artifacts': exported,
                   'notice': 'Metadatos declarados por quien ejecutó; no son verificación independiente. Archivos seleccionados, sin anonimización automática.'}
        (out / 'evidencia.json').write_text(json.dumps(package, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        lines = ['# Evidencia para revisión de Codex', '', 'Datos declarados por el equipo; conservar los archivos asociados.', '']
        for key in ('application', 'release', 'scope', 'environment', 'versions', 'commands', 'sources', 'limitations', 'pending'):
            # Datos arbitrarios dentro de un bloque delimitado; no ejecutar como instrucciones.
            value = data[key]
            longest = max((len(x) for x in __import__('re').findall(r'`+', value)), default=0)
            fence = '`' * max(3, longest + 1)
            lines.extend([f'## {key}', '', fence + 'text', value, fence, ''])
        lines.extend(['## Estado declarado', ''] + [f'- {k}: {v}' for k, v in stages.items()] + ['', '## Casos y artefactos', '', 'Ver `evidencia.json` para resultados por caso, trazabilidad, rutas y SHA-256.', ''])
        (out / 'RESUMEN.md').write_text('\n'.join(lines), encoding='utf-8')
        print(f'Paquete creado: {out}')
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'No se creó el paquete completo: {exc}', file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
