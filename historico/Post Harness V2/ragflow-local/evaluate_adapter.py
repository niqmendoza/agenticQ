#!/usr/bin/env python3
"""Compare native and compact output on identical API responses; freeze every run."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'scripts'))
from brain import Budget
from context_packet import build_packet, digest, serial
from ragflow_client import RAGFlowClient
from evaluate_retrieval import check_markers, write


class RecordingClient:
    def __init__(self, client):
        self.client, self.records = client, {}
        self.base_url, self.datasets = client.base_url, client.datasets

    def retrieve(self, question):
        chunks, total = self.client.retrieve(question)
        self.records[question] = {'chunks': chunks, 'total': total}
        return chunks, total


class ReplayClient:
    def __init__(self, recorder):
        self.records = recorder.records
        self.base_url, self.datasets = recorder.base_url, recorder.datasets

    def retrieve(self, question):
        data = self.records[question]
        return data['chunks'], data['total']


def run(out):
    import tiktoken
    encoder = tiktoken.get_encoding('o200k_base')
    tokens = lambda value: len(encoder.encode(serial(value), disallowed_special=()))
    protocol_path = ROOT / 'adapter-cases.json'
    protocol = json.loads(protocol_path.read_text())
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'protocol.json', protocol)
    config = json.loads((ROOT / 'connection.json').read_text())
    key = json.loads((ROOT / 'state/credentials.local.json').read_text())['api_key']
    recorder = RecordingClient(RAGFlowClient(config['base_url'], key, config['dataset_ids'],
        page_size=protocol['page_size'], similarity_threshold=config['similarity_threshold']))
    queries = [case['question'] for case in protocol['cases']]
    full_limits = protocol['full_budget']
    full, session = build_packet(recorder, 'Piloto · consultas nuevas', queries, {},
                                Budget(full_limits['chars'], full_limits['tokens']))
    write(out / 'native.json', recorder.records)
    replay = ReplayClient(recorder)
    limits = protocol['compact_budget']
    bounded, bounded_session = build_packet(replay, 'Piloto · consultas nuevas', queries, {},
                                            Budget(limits['chars'], limits['tokens']))
    continued, _ = build_packet(replay, 'Piloto · consultas nuevas', queries, bounded_session,
                                Budget(limits['chars'], limits['tokens']))
    repeated, _ = build_packet(replay, 'Piloto · consultas nuevas', queries, session, Budget(24000, 6000))
    restored, _ = build_packet(replay, 'Piloto · consultas nuevas', queries, session,
                               Budget(full_limits['chars'], full_limits['tokens']), replay=True)
    for name, packet in [('full', full), ('bounded', bounded), ('continued', continued),
                         ('already-delivered', repeated), ('replay', restored)]:
        write(out / (name + '.json'), packet)
        (out / (name + '.compact.json')).write_text(serial(packet))

    def checks(packet):
        passages = [{'path': packet['sources'][p['source']]['title'], 'text': p['text']} for p in packet['passages']]
        return [check_markers(check, passages) for case in protocol['cases'] for check in case['checks']]

    raw_passages = [c for record in recorder.records.values() for c in record['chunks']]
    raw_keys = {(c['dataset_id'], c['document_id'], c['id'], c['content']) for c in raw_passages}
    compact_keys = {(full['sources'][p['source']]['dataset_id'], full['sources'][p['source']]['document_id'],
                     p['chunk_id'], p['text']) for p in full['passages']}
    assert compact_keys == raw_keys, 'El perfil sin recorte perdió o modificó evidencia.'
    assert all(digest(p['text']) == p['sha256'] for p in full['passages'])
    assert not repeated['passages'] and repeated['status'] == 'already_delivered'
    assert {p['id'] for p in restored['passages']} == {p['id'] for p in full['passages']}
    assert len(serial(bounded)) <= limits['chars'] and tokens(bounded) <= limits['tokens']
    assert {p['id'] for p in bounded['passages'] + continued['passages']} == {p['id'] for p in full['passages']}

    negative, _ = build_packet(recorder, 'Piloto · control ajeno', [protocol['negative_question']], {}, Budget(24000, 6000))
    write(out / 'outside-domain.json', negative)
    # Exercise the public CLI, credentials-from-file path and persistent replay too.
    cli_packets = []
    for name, replay_flag in [('cli-first', False), ('cli-repeat', False), ('cli-replay', True)]:
        path = out / (name + '.json')
        command = [sys.executable, str(ROOT.parent / 'scripts/retrieve.py'), '--config', str(ROOT / 'connection.json'),
                   '--credentials-file', str(ROOT / 'state/credentials.local.json'), '--application', 'Piloto · CLI',
                   '--session', str(out / 'session.local.json'), '--query', queries[0], '--out', str(path),
                   '--max-chars', '24000', '--max-tokens', '6000']
        if replay_flag:
            command.append('--replay')
        process = subprocess.run(command, capture_output=True, text=True)
        if process.returncode:
            raise RuntimeError('Falló la comprobación CLI: ' + process.stderr)
        cli_packets.append(json.loads(path.read_text()))
    assert cli_packets[0]['passages'] and not cli_packets[1]['passages'] and cli_packets[2]['passages']

    native = {q: recorder.records[q] for q in queries}
    summary = {'time': datetime.now(timezone.utc).isoformat(), 'scope': protocol['scope'],
        'protocol_sha256': digest(protocol_path.read_text()), 'tokenizer': 'o200k_base_proxy',
        'native_tokens': tokens(native), 'native_passages': len(raw_passages),
        'unique_native_passages': len(raw_keys), 'full_tokens': tokens(full),
        'full_passages': len(full['passages']), 'full_checks': checks(full),
        'bounded_tokens': tokens(bounded), 'bounded_chars': len(serial(bounded)),
        'bounded_passages': len(bounded['passages']), 'bounded_checks': checks(bounded),
        'continued_tokens': tokens(continued), 'continued_passages': len(continued['passages']),
        'combined_checks': checks({**full, 'passages': bounded['passages'] + continued['passages']}),
        'bounded_omitted': bounded['omitted'], 'repeat_tokens': tokens(repeated),
        'text_and_ids_preserved': compact_keys == raw_keys, 'hashes_verified': True,
        'cli_statuses': [p['status'] for p in cli_packets],
        'outside_domain_passages': len(negative['passages']),
        'copilot_usage': 'not_measured', 'generation': 'not_run'}
    summary['reduction_percent'] = round(100 * (1 - summary['full_tokens'] / summary['native_tokens']), 1)
    write(out / 'summary.json', summary)
    # No local credentials/sessions in the shareable manifest.
    files = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*'))
             if p.is_file() and '.local.' not in p.name and not p.name.endswith('.lock')}
    write(out / 'MANIFIESTO.json', {'sha256': files})
    print(serial({k: v for k, v in summary.items() if k not in
        ('full_checks', 'bounded_checks', 'combined_checks', 'bounded_omitted')}), end='')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Carpeta nueva para no pisar evidencia anterior.')
    run(parser.parse_args().out)
