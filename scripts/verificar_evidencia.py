#!/usr/bin/env python3
"""Comprueba existencia y hash de artefactos en un paquete de evidencia."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    if len(sys.argv) != 2:
        print('Uso: python3 scripts/verificar_evidencia.py CARPETA_PAQUETE', file=sys.stderr); return 2
    try:
        root = Path(sys.argv[1]).resolve(strict=True)
        package = json.loads((root / 'evidencia.json').read_text(encoding='utf-8'))
        if package.get('schema') != 'qa-evidence-package/1' or not isinstance(package.get('artifacts'), list): raise ValueError('Esquema inválido')
        for item in package['artifacts']:
            rel = Path(item['path'])
            if rel.is_absolute() or '..' in rel.parts: raise ValueError('Ruta inválida')
            current = root
            for part in rel.parts:
                current = current / part
                if current.is_symlink(): raise ValueError('Enlace simbólico no permitido')
            file = current.resolve(strict=True)
            if root not in file.parents or not file.is_file(): raise ValueError('Archivo fuera del paquete')
            digest = hashlib.sha256()
            with file.open('rb') as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b''): digest.update(chunk)
            if digest.hexdigest() != item['sha256'] or file.stat().st_size != item['bytes']: raise ValueError(f'Integridad no coincide: {rel}')
        print(f"Artefactos verificados: {len(package['artifacts'])}. Los metadatos y la autoría no están autenticados.")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'Paquete inválido: {exc}', file=sys.stderr); return 1


if __name__ == '__main__':
    sys.exit(main())
