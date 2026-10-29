#!/usr/bin/env python3
"""Show indexing status or run retrieval with RAGFlow's native response fields."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'scripts'))
from ragflow_client import RAGFlowClient
from setup_api import API, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question')
    parser.add_argument('--save', type=Path)
    args = parser.parse_args()
    try:
        connection = json.loads((ROOT / 'connection.json').read_text())
        credentials = json.loads((ROOT / 'state/credentials.local.json').read_text())
        if args.question:
            client = RAGFlowClient(connection['base_url'], credentials['api_key'], connection['dataset_ids'],
                                   page_size=connection['page_size'], similarity_threshold=connection['similarity_threshold'])
            chunks, total = client.retrieve(args.question)
            result = {'question': args.question, 'total': total, 'chunks': chunks}
        else:
            api = API(connection['base_url'])
            api.auth = credentials['api_key']
            data, _ = api.call('GET', f'/datasets/{connection["dataset_ids"][0]}/documents?page=1&page_size=100')
            docs = data.get('docs', data.get('documents', [])) if isinstance(data, dict) else data
            counts = {}
            for doc in docs:
                state = str(doc.get('run', doc.get('status', 'unknown')))
                counts[state] = counts.get(state, 0) + 1
            result = {'documents': len(docs), 'states': counts,
                      'chunks': sum(doc.get('chunk_count', 0) for doc in docs)}
        if args.save:
            save(args.save, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        print('Consulta incompleta: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
