#!/usr/bin/env python3
"""Small documentary generation experiment. No Azure writes or QA approvals."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:11434'


def api(path, body=None, timeout=120):
    request = Request(BASE + '/api/' + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def inspect_output(text, context):
    result = {'json_valid': False, 'structure_valid': False, 'citation_errors': [],
              'semantic_validation': 'not_performed'}
    try:
        parsed = json.loads(text)
    except ValueError:
        return result
    result['json_valid'] = True
    if not isinstance(parsed, dict) or not isinstance(parsed.get('cases'), list) or not isinstance(parsed.get('open_questions'), list):
        return result
    if len(parsed['cases']) > 3 or not all(isinstance(q, str) for q in parsed['open_questions']):
        return result
    sources = {p['id']: p['text'] for p in context}
    for case in parsed['cases']:
        if not isinstance(case, dict) or not all(isinstance(case.get(k), str) and case[k].strip() for k in ('title', 'expected')):
            return result
        if not all(isinstance(case.get(k), list) and all(isinstance(v, str) for v in case[k]) for k in ('preconditions', 'steps')) or not case['steps']:
            return result
        if not isinstance(case.get('evidence'), list) or not case['evidence']:
            return result
        for citation in case['evidence']:
            if not isinstance(citation, dict):
                return result
            pid, quote = citation.get('passage_id'), citation.get('quote')
            if not isinstance(pid, str) or not isinstance(quote, str) or not quote.strip():
                return result
            if pid not in sources:
                result['citation_errors'].append('unknown_passage')
            elif quote not in sources[pid]:
                result['citation_errors'].append('quote_not_literal')
    result['structure_valid'] = True
    result['case_count'] = len(parsed['cases'])
    result['open_question_count'] = len(parsed['open_questions'])
    return result


def run(out, protocol_file):
    protocol = json.loads(protocol_file.read_text())
    template = json.loads((ROOT / 'generation-request.template.json').read_text())
    installed = api('tags')['models']
    names = {m['name'] for m in installed}
    if not set(protocol['models']) <= names:
        raise ValueError('Falta un modelo del protocolo; este script no descarga modelos.')
    out.mkdir(parents=True, exist_ok=False)
    write(out / 'protocol.json', protocol)
    version = api('version')
    write(out / 'model-identities.json', {'server': version,
        'models': [{k: m.get(k) for k in ('name', 'digest', 'size', 'details')}
                   for m in installed if m['name'] in protocol['models']]})
    summary = {'started_at': datetime.now(timezone.utc).isoformat(),
               'scope': protocol['scope'], 'protocol_sha256': hashlib.sha256(protocol_file.read_bytes()).hexdigest(),
               'runs': [], 'qa_review': 'pending', 'copilot_usage': 'not_used'}
    for model in protocol['models']:
        for case in protocol['cases']:
            label = model.replace(':', '-').replace('.', '_') + '-' + case['id']
            body = {**template, 'model': model, 'options': protocol['settings'], 'keep_alive': 0,
                    'format': protocol.get('format', template['format']),
                    'messages': [template['messages'][0], {'role': 'user', 'content': json.dumps(
                        {'task': case['task'], 'context': case['context']}, ensure_ascii=False)}]}
            write(out / (label + '.request.json'), body)
            stop = threading.Event()
            samples = []

            def sample():
                while not stop.is_set():
                    try:
                        for loaded in api('ps', timeout=2).get('models', []):
                            if loaded.get('name') == model:
                                samples.append({k: loaded.get(k) for k in ('size', 'size_vram', 'context_length')})
                    except (OSError, ValueError):
                        pass
                    stop.wait(0.2)

            watcher = threading.Thread(target=sample, daemon=True)
            watcher.start()
            started = time.perf_counter()
            print('Ejecutando: ' + label, flush=True)
            record = {'model': model, 'case': case['id']}
            try:
                response = api('chat', body)
                content = response.get('message', {}).get('content', '')
                # Save final content and native usage, never a model's thinking field.
                record.update({k: response.get(k) for k in ('model', 'done', 'done_reason', 'total_duration',
                    'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration')})
                record['content'] = content
                record['checks'] = inspect_output(content, case['context'])
            except (OSError, ValueError) as error:
                record['error'] = type(error).__name__
            finally:
                stop.set()
                watcher.join(timeout=3)
            record['seconds'] = round(time.perf_counter() - started, 3)
            record['max_sampled_ollama_size_bytes'] = max((s.get('size') or 0 for s in samples), default=None)
            record['max_sampled_ollama_vram_bytes'] = max((s.get('size_vram') or 0 for s in samples), default=None)
            record['memory_samples'] = len(samples)
            write(out / (label + '.response.json'), record)
            summary['runs'].append({k: v for k, v in record.items() if k != 'content'})
            print(json.dumps(summary['runs'][-1], ensure_ascii=False), flush=True)
    write(out / 'summary.json', summary)
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.json'))}
    write(out / 'MANIFIESTO.json', {'sha256': files})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, default=ROOT / 'small-model-cases.json')
    args = parser.parse_args()
    run(args.out, args.protocol)
