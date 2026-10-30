#!/usr/bin/env python3
"""Run the public retrieval and drafting CLIs on a fixed local pilot protocol."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
V2 = ROOT.parent


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(out):
    protocol = json.loads((ROOT / 'grounded-cases.json').read_text())
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'protocol.json', protocol)
    with urlopen('http://127.0.0.1:11434/api/tags', timeout=5) as response:
        models = json.load(response)['models']
    write(out / 'model-identity.json', [{k: model.get(k) for k in ('name', 'digest', 'size', 'details')}
          for model in models if model['name'] == protocol['model']])
    summary = {'started_at': datetime.now(timezone.utc).isoformat(), 'scope': protocol['scope'], 'runs': []}
    for case in protocol['cases']:
        folder = out / case['id']
        folder.mkdir()
        write(folder / 'task.json', case['task'])
        commands = [[sys.executable, str(V2 / 'scripts/retrieve.py'),
            '--config', str(V2 / 'ragflow-local/connection.json'),
            '--credentials-file', str(V2 / 'ragflow-local/state/credentials.local.json'),
            '--application', 'Piloto de generación 4B', '--session', str(folder / 'retrieval.local.json'),
            '--query', case['query'], '--page-size', str(protocol['retrieval_page_size']),
            '--max-chars', '24000', '--out', str(folder / 'context.json')],
            [sys.executable, str(V2 / 'scripts/draft_cases.py'), '--context', str(folder / 'context.json'),
             '--task', str(folder / 'task.json'), '--model', protocol['model'], '--out', str(folder / 'generation')]]
        record = {'id': case['id'], 'status': 'not_started'}
        print('Ejecutando flujo: ' + case['id'], flush=True)
        for command in commands:
            process = subprocess.run(command, capture_output=True, text=True)
            if process.returncode:
                record.update({'status': 'failed', 'stderr': process.stderr.strip()})
                break
            record['status'] = 'completed'
        if record['status'] == 'completed':
            result = json.loads((folder / 'generation/drafts.json').read_text())
            trace = json.loads((folder / 'generation/trace.json').read_text())
            record.update({'state': result['state'], 'cases': len(result['cases']),
                'questions': len(result['open_questions']), 'selected_rule_ids': result.get('selected_rule_ids', []),
                'model_calls': len(trace), 'prompt_tokens_native': sum(t['native_usage'].get('prompt_eval_count') or 0 for t in trace),
                'output_tokens_native': sum(t['native_usage'].get('eval_count') or 0 for t in trace),
                'qa_review': result['qa_review']})
        summary['runs'].append(record)
        write(out / 'summary.json', summary)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    files = {str(path.relative_to(out)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(out.rglob('*'))
             if path.is_file() and '.local.' not in path.name and not path.name.endswith('.lock')}
    write(out / 'MANIFIESTO.json', {'sha256': files})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
