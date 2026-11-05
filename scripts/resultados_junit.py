#!/usr/bin/env python3
"""Relaciona resultados JUnit con casos mediante correspondencias explícitas."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--junit', required=True); p.add_argument('--map', required=True); p.add_argument('--out', required=True)
    args = p.parse_args()
    try:
        source = Path(args.junit); raw = source.read_bytes()
        if len(raw) > 10_000_000: raise ValueError('XML demasiado grande')
        text = raw.decode('utf-8-sig')
        if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper(): raise ValueError('XML con declaraciones o codificación no admitidas')
        root = ET.fromstring(text)
        if root.tag.rsplit('}', 1)[-1] not in ('testsuite', 'testsuites'): raise ValueError('Raíz JUnit no reconocida')
        mapping = json.loads(Path(args.map).read_text(encoding='utf-8'))
        if not isinstance(mapping, dict) or not mapping: raise ValueError('El mapa debe contener casos')
        keys = []
        for cid, spec in mapping.items():
            if not isinstance(cid, str) or not cid.strip() or not isinstance(spec, dict) or not all(isinstance(spec.get(k), str) and spec[k].strip() for k in ('classname','name')): raise ValueError('Mapa inválido')
            keys.append((spec['classname'],spec['name']))
        if len(set(keys)) != len(keys): raise ValueError('Una prueba no puede asociarse a más de un caso')
        observed = {}
        for element in root.iter():
            if element.tag.rsplit('}', 1)[-1] != 'testcase': continue
            key = (element.get('classname'), element.get('name'))
            observed.setdefault(key, []).append(element)
        digest = hashlib.sha256(raw).hexdigest()
        results, executed, evidence = {}, {}, {}
        for cid, spec in mapping.items():
            key = (spec['classname'], spec['name']); found = observed.get(key, [])
            reference = f"JUnit SHA-256 {digest}; {key[0]}::{key[1]}"
            evidence[cid] = reference
            if len(found) != 1:
                results[cid] = 'Sin resultado individual' if not found else 'Resultado ambiguo: prueba repetida en JUnit'
                executed[cid] = 'Sin evidencia de ejecución individual' if not found else 'Correspondencia ambigua'
                continue
            el = found[0]; statuses = [child.tag.rsplit('}',1)[-1] for child in el if child.tag.rsplit('}',1)[-1] in ('failure','error','skipped')]
            status = el.get('status', '').lower()
            if len(statuses) > 1 or status not in ('', 'run', 'completed'):
                results[cid] = 'Sin resultado individual: estado JUnit ambiguo'; executed[cid] = 'Sin evidencia de ejecución individual'
            elif statuses == ['skipped']:
                results[cid] = 'Omitida'; executed[cid] = 'No ejecutada: omitida por el framework'
            else:
                results[cid] = 'Falló' if statuses else 'Aprobada'
                executed[cid] = f'{key[0]}::{key[1]}'
        out = Path(args.out); out.mkdir(mode=0o700, parents=False, exist_ok=False)
        for name, data in [('resultados.json', results), ('ejecutadas.json', executed), ('evidencias.json', evidence)]:
            (out/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(f'Resultados preparados: {out}; conservar el XML original.')
        return 0
    except (OSError, ValueError, TypeError, KeyError, ET.ParseError) as exc:
        print(f'No se pudo procesar JUnit: {exc}', file=sys.stderr); return 2


if __name__ == '__main__':
    sys.exit(main())
