#!/usr/bin/env python3
"""Compare relevance cutoffs on fixed pilot queries; no automatic configuration change."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'scripts'))
from ragflow_client import RAGFlowClient
from evaluate_retrieval import Capture, check_markers, serial, write


def main():
    import tiktoken
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    config = json.loads((ROOT / 'connection.json').read_text())
    key = json.loads((ROOT / 'state/credentials.local.json').read_text())['api_key']
    imported = json.loads((ROOT / 'state/corpus.local.json').read_text())
    paths = {record['id']: name for name, record in imported['documents'].items()}
    cases = json.loads((ROOT / 'retrieval-cases.json').read_text())['cases']
    negatives = [
        '¿Cuál es el itinerario de la expedición submarina del planeta ficticio Nébula X?',
        '¿Cómo preparo masa madre de harina de centeno?',
        '¿Qué fecha tiene la coronación de la reina del reino imaginario Brumalia?',
        '¿Qué receta de pan usa el chat para fermentar masa madre?'
    ]
    protocol = {'started_at': datetime.now(timezone.utc).isoformat(),
                'thresholds': [0.2, 0.28, 0.3], 'page_size': 5, 'cases': cases,
                'negative_questions': negatives,
                'scope': 'Calibración posterior al ensayo inicial. Controles ficticios seleccionados manualmente; no demuestra abstención general.'}
    write(out / 'protocol.json', protocol)
    encoder = tiktoken.get_encoding('o200k_base')
    results = []
    for threshold in protocol['thresholds']:
        client = RAGFlowClient(config['base_url'], key, config['dataset_ids'], page_size=5, similarity_threshold=threshold)
        checks = []
        payload_tokens = 0
        for case in cases:
            record = {}
            client.opener = Capture(client.opener if not isinstance(client.opener, Capture) else client.opener.opener, record)
            chunks, total = client.retrieve(case['question'])
            write(out / 'raw' / f'{threshold}-{case["id"]}.json', record)
            passages = [{'path': paths[c['document_id']], 'text': c['content']} for c in chunks]
            checks.extend(check_markers(check, passages) for check in case['checks'])
            payload_tokens += len(encoder.encode(serial({'chunks': chunks, 'total': total}), disallowed_special=()))
        controls = []
        for i, question in enumerate(negatives):
            record = {}
            client.opener = Capture(client.opener.opener, record)
            chunks, total = client.retrieve(question)
            write(out / 'raw' / f'{threshold}-outside-{i}.json', record)
            controls.append({'question': question, 'chunks': len(chunks),
                             'scores': [c.get('similarity') for c in chunks],
                             'sources': [paths[c['document_id']] for c in chunks]})
        results.append({'threshold': threshold, 'checks_matched': sum(c['matched'] for c in checks),
                        'checks_total': len(checks), 'checks': checks, 'client_tokens': payload_tokens,
                        'controls_empty': sum(c['chunks'] == 0 for c in controls), 'controls_total': len(controls),
                        'controls': controls})
    summary = {'protocol': protocol, 'profiles': results, 'configuration_changed': False}
    write(out / 'summary.json', summary)
    print(json.dumps([{k: v for k, v in p.items() if k not in ('checks', 'controls')} for p in results], indent=2))


if __name__ == '__main__':
    main()
