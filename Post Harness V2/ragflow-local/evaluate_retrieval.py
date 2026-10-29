#!/usr/bin/env python3
"""Reproducible retrieval regression. No generation or Copilot billing claims."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import sys
import time
import unicodedata
import re

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
sys.path.insert(0, str(ROOT.parent / 'scripts'))
import brain
from ragflow_client import RAGFlowClient, RetrievalError
from setup_api import API, corpus_files


def text_key(text):
    text = unicodedata.normalize('NFKD', text).casefold()
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def serial(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def check_markers(check, passages):
    # Presence of these cues is a regression signal, not semantic entailment.
    relevant = [p['text'] for p in passages if Path(p['path']).name == check['document']]
    raw = '\n'.join(relevant)
    normal = text_key(raw)
    missing = [s for s in check.get('contains', []) if text_key(s) not in normal]
    missing += [s for s in check.get('literal', []) if s not in raw]
    return {'id': check['id'], 'title': check['title'], 'document': check['document'],
            'source_present': bool(relevant), 'matched': bool(relevant) and not missing,
            'missing_markers': missing}


def fingerprint(chunk):
    return hashlib.sha256(serial([chunk.get('dataset_id'), chunk.get('document_id'),
                                 chunk.get('id'), chunk.get('content')]).encode()).hexdigest()


class CapturedResponse:
    def __init__(self, response, record):
        self.response, self.record = response, record

    def __enter__(self):
        self.response.__enter__()
        return self

    def __exit__(self, *args):
        return self.response.__exit__(*args)

    def read(self, limit):
        raw = self.response.read(limit)
        self.record['response'] = json.loads(raw)
        self.record['response_bytes'] = len(raw)
        return raw


class Capture:
    def __init__(self, opener, record):
        self.opener, self.record = opener, record

    def open(self, request, **kwargs):
        # Explicit allowlist: never record headers or a request object's repr.
        self.record['request'] = json.loads(request.data)
        return CapturedResponse(self.opener.open(request, **kwargs), self.record)


def run(args):
    import tiktoken
    encoder = tiktoken.get_encoding('o200k_base')
    tokens = lambda s: len(encoder.encode(s, disallowed_special=()))
    config = json.loads((ROOT / 'connection.json').read_text())
    credentials = json.loads((ROOT / 'state/credentials.local.json').read_text())
    protocol_path = ROOT / 'retrieval-cases.json'
    protocol = json.loads(protocol_path.read_text())
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    # Freeze checks before retrieving any result from this run.
    write(out / 'protocol.json', protocol)
    started = datetime.now(timezone.utc).isoformat()
    files = corpus_files(WORKSPACE / 'Post Harness/evidencias/fuentes')
    inventory = {relative: {'text': path.read_text(), 'sha256': sha} for relative, path, sha in files}
    imported = json.loads((ROOT / 'state/corpus.local.json').read_text())
    paths = {value['id']: relative for relative, value in imported['documents'].items()}
    if set(paths.values()) != set(inventory):
        raise RuntimeError('Los documentos importados no coinciden con los 80 del corpus verificado.')
    api = API(config['base_url'])
    api.auth = credentials['api_key']
    data, _ = api.call('GET', '/datasets/' + config['dataset_ids'][0] + '/documents?page=1&page_size=100')
    if len(data['docs']) != len(files) or any(d['run'] != 'DONE' for d in data['docs']):
        raise RuntimeError('El corpus no terminó de procesarse; no evaluar con documentos pendientes.')
    summary = {'started_at': started, 'protocol_sha256': hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
               'scope': protocol['scope'], 'tokenizer': 'tiktoken/o200k_base proxy',
               'corpus': {'documents': len(files), 'chunks': sum(d.get('chunk_count', 0) for d in data['docs']),
                          'source_tokens': sum(tokens(v['text']) for v in inventory.values())},
               'profiles': {}, 'controls': {}, 'copilot_usage': 'not_measured', 'generation': 'not_run'}

    def client(page_size=5, key=None, dataset_ids=None):
        return RAGFlowClient(config['base_url'], key or credentials['api_key'],
                             dataset_ids or config['dataset_ids'], page_size=page_size,
                             similarity_threshold=config['similarity_threshold'])

    def retrieve(label, case_id, question, page_size):
        c = client(page_size)
        record = {}
        c.opener = Capture(c.opener, record)
        start = time.perf_counter()
        chunks, total = c.retrieve(question)
        elapsed = time.perf_counter() - start
        record['seconds'] = elapsed
        record['client_output'] = {'chunks': chunks, 'total': total}
        write(out / 'raw' / f'{label}-{case_id}.json', record)
        passages = []
        for chunk in chunks:
            if chunk.get('dataset_id') not in config['dataset_ids'] or chunk.get('document_id') not in paths:
                raise RuntimeError('RAGFlow devolvió evidencia fuera del dataset y corpus permitidos.')
            if not all(isinstance(chunk.get(k), str) and chunk[k] for k in ('id', 'content')):
                raise RuntimeError('Fragmento sin identidad o contenido.')
            path = paths[chunk['document_id']]
            passages.append({'path': path, 'text': chunk['content'], 'fingerprint': fingerprint(chunk),
                             'normalized_text_is_substring': text_key(chunk['content']) in text_key(inventory[path]['text'])})
        return {'question': question, 'seconds': elapsed, 'total_candidates': total,
                'chunks': len(chunks), 'paths': sorted(set(p['path'] for p in passages)),
                'client_tokens': tokens(serial(record['client_output'])),
                'transport_tokens': tokens(serial(record['response'])),
                'text_tokens': sum(tokens(c['content']) for c in chunks),
                'response_bytes': record['response_bytes'], 'passages': passages}

    for profile in protocol['profiles']:
        name = profile['name']
        first = [retrieve(name, case['id'], case['question'], profile['page_size']) for case in protocol['cases']]
        # Repeat the same five queries: measure result identity, not byte equality of scores/times.
        repeated = [retrieve(name + '-repeat', case['id'], case['question'], profile['page_size']) for case in protocol['cases']]
        checks = [check_markers(check, result['passages']) for case, result in zip(protocol['cases'], first) for check in case['checks']]
        all_passages = [p for result in first for p in result['passages']]
        duplicates = len(all_passages) - len({p['fingerprint'] for p in all_passages})
        summary['profiles'][name] = {
            'page_size': profile['page_size'], 'queries': first, 'checks': checks,
            'checks_matched': sum(check['matched'] for check in checks), 'checks_total': len(checks),
            'client_tokens': sum(r['client_tokens'] for r in first),
            'transport_tokens': sum(r['transport_tokens'] for r in first),
            'text_tokens': sum(r['text_tokens'] for r in first),
            'unique_documents': len({p['path'] for p in all_passages}),
            'duplicate_passages_across_queries': duplicates,
            'repeat_same_passage_sets': all({p['fingerprint'] for p in a['passages']} == {p['fingerprint'] for p in b['passages']} for a, b in zip(first, repeated)),
            'first_pass_seconds': sum(r['seconds'] for r in first),
            'repeat_seconds': sum(r['seconds'] for r in repeated)}

    # Same V2 parameters, fresh index/session: preserve all historical evidence.
    local_db = out / 'local/indice.sqlite'
    local_db.parent.mkdir()
    brain.index(WORKSPACE / 'Post Harness/evidencias/fuentes', local_db)
    connection, cfg, settings = brain.checked(local_db)
    try:
        local_start = time.perf_counter()
        packet = brain.pack(connection, cfg, settings, brain.session_load(None, cfg['revision']),
                            [c['question'] for c in protocol['cases']], brain.Budget(50000, 14000),
                            seeds=2, related=5, max_docs=20, max_lines=120)
        elapsed = time.perf_counter() - local_start
    finally:
        connection.close()
    write(out / 'local/packet.json', packet)
    local_passages = [{'path': packet['sources'][p['source']]['path'],
                       'text': '\n'.join(line.split('|', 1)[1] for line in p['text'].splitlines())}
                      for p in packet['passages']]
    local_checks = [check_markers(check, local_passages) for case in protocol['cases'] for check in case['checks']]
    summary['profiles']['local-v2'] = {'checks': local_checks, 'checks_matched': sum(c['matched'] for c in local_checks),
        'checks_total': len(local_checks), 'client_tokens': tokens(brain.dump(packet)),
        'text_tokens': sum(tokens(p['text']) for p in local_passages),
        'unique_documents': len(packet['sources']), 'pending_total': packet['pending_total'], 'seconds': elapsed}

    # Targeted expansions are separately labelled: test-specific hints, not autonomous discovery.
    base = summary['profiles']['ragflow-5']
    checks_by_id = {check['id']: check for check in base['checks']}
    expansions = []
    combined = {case['id']: list(result['passages']) for case, result in zip(protocol['cases'], base['queries'])}
    for case in protocol['cases']:
        for check in case['checks']:
            if checks_by_id[check['id']]['matched']:
                continue
            if len(expansions) >= protocol['followups']['max_calls']:
                break
            result = retrieve('directed', check['id'], check['followup'], protocol['followups']['page_size'])
            expansions.append(result)
            combined[case['id']].extend(result['passages'])
    directed_checks = [check_markers(check, combined[case['id']]) for case in protocol['cases'] for check in case['checks']]
    summary['profiles']['ragflow-5-directed'] = {'checks': directed_checks,
        'checks_matched': sum(c['matched'] for c in directed_checks), 'checks_total': len(directed_checks),
        'extra_calls': len(expansions), 'client_tokens': base['client_tokens'] + sum(r['client_tokens'] for r in expansions),
        'text_tokens': base['text_tokens'] + sum(r['text_tokens'] for r in expansions), 'expansions': expansions}

    for name, c in [('invalid_key', client(key='ragflow-invalid-regression-key')),
                    ('unknown_dataset', client(dataset_ids=['0' * 32]))]:
        try:
            chunks, total = c.retrieve('permisos')
            summary['controls'][name] = {'result': 'empty' if not chunks else 'unexpected_evidence', 'total': total}
            if chunks:
                raise RuntimeError('Una credencial o dataset inválido devolvió evidencia.')
        except RetrievalError as error:
            summary['controls'][name] = {'result': 'rejected', 'error': str(error)}
    with socket.socket() as bound:
        bound.bind(('127.0.0.1', 0))
        disconnected = RAGFlowClient(f'http://127.0.0.1:{bound.getsockname()[1]}', 'test-only', config['dataset_ids'], timeout=1)
        try:
            disconnected.retrieve('consulta')
            raise RuntimeError('El endpoint sin servicio no produjo un error.')
        except RetrievalError as error:
            summary['controls']['unavailable_service'] = {'result': 'explicit_error', 'error': str(error)}
    negative = retrieve('control', 'outside-domain', protocol['negative_question'], 5)
    summary['controls']['outside_domain'] = negative
    summary['finished_at'] = datetime.now(timezone.utc).isoformat()
    write(out / 'summary.json', summary)
    print(serial({'output': str(out), 'profiles': {name: {k: v for k, v in p.items() if k in
        ('checks_matched', 'checks_total', 'client_tokens', 'text_tokens', 'extra_calls', 'repeat_same_passage_sets')}
        for name, p in summary['profiles'].items()}, 'controls': {name: {k: v for k, v in item.items()
        if k in ('result', 'error', 'chunks', 'total_candidates', 'client_tokens')}
        for name, item in summary['controls'].items()}}), end='')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Nueva carpeta para preservar cada ejecución.')
    args = parser.parse_args()
    run(args)


if __name__ == '__main__':
    main()
