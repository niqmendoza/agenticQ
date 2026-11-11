#!/usr/bin/env python3
"""Check packet references, hashes and serialized limits, not functional truth."""
import argparse
import sys

from brain import Budget
from context_packet import SCHEMA, digest, serial
from retrieve import read_json


def verify(packet):
    if not isinstance(packet, dict) or packet.get('schema') != SCHEMA or packet.get('coverage') != 'not_asserted':
        raise ValueError('Formato o declaración de cobertura inválidos.')
    sources, passages, queries = packet['sources'], packet['passages'], packet['queries']
    if not isinstance(sources, dict) or not isinstance(passages, list) or not isinstance(queries, list):
        raise ValueError('Fuentes, fragmentos o consultas inválidos.')
    query_ids = {q['id'] for q in queries}
    if len(query_ids) != len(queries):
        raise ValueError('Hay identificadores de consulta repetidos.')
    for sid, source in sources.items():
        expected = 'S' + digest(serial([packet['origin'], source['dataset_id'], source['document_id']]))[:16]
        if sid != expected:
            raise ValueError('Una fuente no coincide con su identificador.')
    ids = set()
    referenced_sources = set()
    for passage in passages:
        source = passage['source']
        if source not in sources or not isinstance(passage['text'], str) or not passage['text']:
            raise ValueError('Un fragmento no tiene texto o referencia una fuente inexistente.')
        sha = digest(passage['text'])
        expected = 'P' + digest(serial([source, passage['chunk_id'], sha]))[:24]
        if passage['sha256'] != sha or passage['id'] != expected or expected in ids:
            raise ValueError('Hash, identificador o unicidad de fragmento inválidos.')
        if not passage['queries'] or not set(passage['queries']) <= query_ids:
            raise ValueError('Un fragmento referencia una consulta inexistente.')
        ids.add(expected)
        referenced_sources.add(source)
    if referenced_sources != set(sources):
        raise ValueError('Hay fuentes sin fragmentos entregados.')
    limits = packet['limits']
    budget = Budget(limits['max_chars'], limits['max_tokens'])
    if not budget.fits(packet):
        raise ValueError('El paquete excede los límites declarados.')
    chars, tokens = budget.size(packet)
    return {'schema': SCHEMA, 'integrity': 'ok', 'passages': len(passages), 'sources': len(sources),
            'chars': chars, 'tokens_proxy': tokens, 'semantic_validation': 'not_performed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packet')
    args = parser.parse_args()
    try:
        print(serial(verify(read_json(args.packet))), end='')
        return 0
    except (ValueError, OSError, KeyError, TypeError):
        print('Paquete inválido o incompleto: revisar referencias, hashes, límites y entorno de Python.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
