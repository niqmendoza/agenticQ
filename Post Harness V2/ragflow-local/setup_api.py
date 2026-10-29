#!/usr/bin/env python3
"""Provision the local RAGFlow test account, embedding provider and frozen corpus.

All writes target this local test instance. It never generates cases or sends
documents to a hosted model. Credentials remain in state/credentials.local.json.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    with open(temporary, 'w', opener=lambda name, flags: __import__('os').open(name, flags, 0o600)) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    temporary.chmod(0o600)
    temporary.replace(path)


class API:
    def __init__(self, base_url):
        self.base = base_url.rstrip('/') + '/api/v1'
        self.auth = None

    def call(self, method, path, body=None, *, content_type='application/json', timeout=60):
        data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
        headers = {'Content-Type': content_type}
        if self.auth:
            headers['Authorization'] = 'Bearer ' + self.auth
        request = Request(self.base + path, method=method, data=data, headers=headers)
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.load(response)
                auth = response.headers.get('Authorization')
        except HTTPError as error:
            raise RuntimeError(f'{method} {path.split("?")[0]}: HTTP {error.code}') from None
        except (URLError, OSError, TimeoutError):
            raise RuntimeError('La API local no está disponible o agotó el tiempo de espera.') from None
        if not isinstance(result, dict) or result.get('code') != 0:
            message = str(result.get('message', 'respuesta inesperada'))[:300] if isinstance(result, dict) else 'respuesta inesperada'
            if self.auth:
                message = message.replace(self.auth, '[credencial]')
            raise RuntimeError(f'{method} {path.split("?")[0]}: {message}')
        return result.get('data'), auth


def encrypted_password(password):
    # Match the official client: RSA PKCS#1 v1.5 over base64(password).
    public_key = ROOT / 'upstream/public.pem'
    result = subprocess.run(['openssl', 'pkeyutl', '-encrypt', '-pubin', '-inkey', str(public_key),
                             '-pkeyopt', 'rsa_padding_mode:pkcs1'],
                            input=base64.b64encode(password.encode()), capture_output=True, check=True)
    return base64.b64encode(result.stdout).decode()


def connect(api):
    path = ROOT / 'state/credentials.local.json'
    if path.exists():
        credentials = json.loads(path.read_text())
    else:
        credentials = {'email': 'qa-piloto@local.test', 'nickname': 'QA Piloto',
                       'password': secrets.token_urlsafe(24), 'registered': False}
        save(path, credentials)
    payload = {'email': credentials['email'], 'password': encrypted_password(credentials['password'])}
    if not credentials.get('registered'):
        _, auth = api.call('POST', '/users', {**payload, 'nickname': credentials['nickname']})
        credentials['registered'] = True
        save(path, credentials)
    else:
        _, auth = api.call('POST', '/auth/login', payload)
    if not auth:
        raise RuntimeError('El inicio de sesión no devolvió una autorización.')
    api.auth = auth.removeprefix('Bearer ')
    if not credentials.get('api_key'):
        token, _ = api.call('POST', '/system/tokens?name=qa-retrieval-local')
        credentials['api_key'] = token['token']
        save(path, credentials)
    return credentials


def embedding(api):
    providers, _ = api.call('GET', '/providers')
    if not any(p.get('provider_name', p.get('name')) == 'Ollama' for p in providers):
        api.call('PUT', '/providers', {'provider_name': 'Ollama'})
    instances, _ = api.call('GET', '/providers/Ollama/instances')
    name = 'qa_local_embeddings'
    if not any(p.get('instance_name', p.get('name')) == name for p in instances):
        api.call('POST', '/providers/Ollama/instances', {
            'instance_name': name, 'api_key': '', 'region': '',
            'base_url': 'http://host.docker.internal:11434',
            'model_info': [{'model_name': 'nomic-embed-text:latest', 'model_type': ['embedding'], 'max_tokens': 8192}]}, timeout=120)
    return 'nomic-embed-text:latest@' + name + '@Ollama'


def corpus_files(corpus):
    inventory = json.loads((WORKSPACE / 'Post Harness/evidencias/inventario.json').read_text())
    files = []
    for source in inventory['files']:
        if not source['included']:
            continue
        path = corpus / source['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise RuntimeError('El corpus no coincide con el snapshot medido: ' + source['path'])
        files.append((source['path'], path, source['sha256']))
    return files


def upload(api, dataset, relative, path):
    boundary = 'qa-' + secrets.token_hex(12)
    # Preserve the original path in RAGFlow's parent_path; use a plain basename.
    parent = str(Path(relative).parent).replace('\\', '/')
    name = path.name.replace('"', '_').replace('\r', '').replace('\n', '')
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="parent_path"\r\n\r\n{parent}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
            'Content-Type: text/markdown; charset=utf-8\r\n\r\n').encode() + path.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
    docs, _ = api.call('POST', f'/datasets/{dataset}/documents', body,
                       content_type='multipart/form-data; boundary=' + boundary)
    if not isinstance(docs, list) or len(docs) != 1 or not docs[0].get('id'):
        raise RuntimeError('La carga no devolvió un documento identificable.')
    return docs[0]['id']


def provision(args):
    api = API(args.base_url)
    version, _ = api.call('GET', '/system/version')
    files = corpus_files(Path(args.corpus).resolve())
    credentials = connect(api)
    print('API disponible; cuenta local y credencial de API preparadas.', flush=True)
    model = embedding(api)
    print('Proveedor de embeddings local configurado.', flush=True)
    state_path = ROOT / 'state/corpus.local.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'documents': {}}
    if not state.get('dataset_id'):
        dataset, _ = api.call('POST', '/datasets', {
            'name': 'Segundo cerebro · piloto Post Harness', 'permission': 'me',
            'description': 'Copia verificada del corpus de 80 Markdown utilizado en el ensayo Post Harness.',
            'language': 'Spanish', 'embedding_model': model, 'chunk_method': 'naive',
            'parser_config': {'chunk_token_num': 512, 'auto_keywords': 0, 'auto_questions': 0,
                              'layout_recognize': 'Plain Text'}})
        state['dataset_id'] = dataset['id']
        state['base_url'] = args.base_url
        save(state_path, state)
    dataset_id = state['dataset_id']
    for index, (relative, path, checksum) in enumerate(files, 1):
        record = state['documents'].get(relative)
        if record:
            if record['sha256'] != checksum:
                raise RuntimeError('La fuente cambió; usar un dataset de nueva revisión.')
            continue
        ident = upload(api, dataset_id, relative, path)
        state['documents'][relative] = {'id': ident, 'sha256': checksum}
        save(state_path, state)
        print(f'Documentos cargados: {index}/{len(files)}', flush=True)
    if not state.get('parsing_requested'):
        ids = [d['id'] for d in state['documents'].values()]
        api.call('POST', f'/datasets/{dataset_id}/documents/parse', {'document_ids': ids})
        state['parsing_requested'] = True
        save(state_path, state)
    config = {'base_url': args.base_url, 'dataset_ids': [dataset_id], 'page_size': 5,
              'similarity_threshold': 0.2, 'api_key_env': 'RAGFLOW_API_KEY'}
    (ROOT / 'connection.json').write_text(json.dumps(config, indent=2) + '\n')
    print('Carga completa; procesamiento solicitado. Las consultas se habilitan al terminar la indexación.', flush=True)
    api.auth = credentials['api_key']
    docs, _ = api.call('GET', f'/datasets/{dataset_id}/documents?page=1&page_size=100')
    save(ROOT / 'state/last-status.local.json', docs)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:9388')
    parser.add_argument('--corpus', default=str(WORKSPACE / 'Post Harness/evidencias/fuentes'))
    args = parser.parse_args()
    try:
        return provision(args)
    except (ValueError, OSError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        print('Configuración incompleta: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
