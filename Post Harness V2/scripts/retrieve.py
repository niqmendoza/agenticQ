#!/usr/bin/env python3
"""Retrieve compact RAGFlow evidence. Never calls a generative model or publishes cases."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import sys
import tempfile

from brain import Budget
from context_packet import SCHEMA, build_packet, digest, serial
from ragflow_client import RAGFlowClient


def read_json(path):
    path = Path(path)
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('El archivo JSON supera 8 MiB.')
    return json.loads(path.read_text(encoding='utf-8'))


def validate_queries(queries):
    if not isinstance(queries, list) or not 1 <= len(queries) <= 20 or not all(
            isinstance(q, str) and q.strip() and len(q) <= 2000 for q in queries):
        raise ValueError('Definir entre 1 y 20 consultas no vacías de hasta 2000 caracteres.')
    return queries


@contextmanager
def session_lock(path):
    """Per-task process lock; fail quickly instead of losing concurrent deliveries."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + '.lock')
    with open(lock_path, 'a', encoding='utf-8') as handle:
        os.chmod(lock_path, 0o600)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('La sesión está en uso; esperar o usar otra sesión por tarea.') from None
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def atomic_text(path, text, *, replace):
    """Private temp file, then atomic installation; output files never overwrite evidence."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)  # Fails atomically if someone else created the output.
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def execute(args, *, stream=None):
    if not args.application.strip() or len(args.application) > 200:
        raise ValueError('application debe identificar una aplicación con 1 a 200 caracteres.')
    queries = validate_queries(read_json(args.queries_json) if args.queries_json else args.query)
    budget = Budget(args.max_chars, args.max_tokens)
    config = read_json(args.config)
    if not isinstance(config, dict):
        raise ValueError('Configuración de conexión inválida.')
    key_env = config.get('api_key_env', 'RAGFLOW_API_KEY')
    key = os.environ.get(key_env, '')
    if args.credentials_file:
        credentials = read_json(args.credentials_file)
        key = credentials.get('api_key', '')
    client = RAGFlowClient(config['base_url'], key, config['dataset_ids'],
                           timeout=config.get('timeout', 30), page_size=getattr(args, 'page_size', None) or config.get('page_size', 5),
                           similarity_threshold=config.get('similarity_threshold', 0.2),
                           allow_insecure_http=config.get('allow_insecure_http', False))
    session_path = Path(args.session).resolve()
    protected = {Path(p).resolve() for p in (args.config, args.queries_json, args.credentials_file) if p}
    output_path = Path(args.out).resolve() if args.out else None
    lock_path = session_path.with_name(session_path.name + '.lock')
    if session_path in protected or lock_path in protected or output_path in protected | {session_path, lock_path}:
        raise ValueError('Sesión, salida y archivos de entrada deben tener rutas distintas.')
    if output_path and output_path.exists():
        raise ValueError('La salida ya existe; usar otro archivo para conservar las evidencias.')
    scope = digest(serial([client.base_url, client.datasets, args.application]))
    with session_lock(session_path):
        session = {'schema': SCHEMA, 'scope': scope, 'delivered': []}
        if session_path.exists():
            session = read_json(session_path)
            if not isinstance(session, dict) or session.get('schema') != SCHEMA or session.get('scope') != scope:
                raise ValueError('La aplicación o la fuente cambió: usar una sesión nueva.')
            if not isinstance(session.get('delivered'), list) or not all(
                    isinstance(p, str) and len(p) == 25 and p.startswith('P') for p in session['delivered']):
                raise ValueError('Registro de entregas de la sesión inválido.')
        packet, updated = build_packet(client, args.application, queries, session, budget, replay=args.replay)
        payload = serial(packet)
        if output_path:
            atomic_text(output_path, payload, replace=False)
        else:
            output = stream if stream is not None else sys.stdout
            if output.write(payload) != len(payload):
                raise OSError('Salida incompleta; la sesión no se actualizó.')
            output.flush()
        # Commit only AFTER a complete output was emitted/saved. A failed commit may
        # repeat evidence next time, but can never hide an undelivered passage.
        atomic_text(session_path, serial(updated), replace=True)
    return packet


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, help='JSON de conexión sin secretos.')
    parser.add_argument('--application', required=True)
    parser.add_argument('--session', required=True, help='Una sesión por tarea; no compartir entre agentes.')
    queries = parser.add_mutually_exclusive_group(required=True)
    queries.add_argument('--query', action='append', help='Repetir para agregar consultas dirigidas.')
    queries.add_argument('--queries-json', help='Archivo con una lista de consultas.')
    parser.add_argument('--credentials-file', help='Sólo para pruebas locales; JSON con api_key. En empresa usar entorno.')
    parser.add_argument('--max-chars', type=int, default=24000)
    parser.add_argument('--max-tokens', type=int, help='Opcional: requiere tiktoken; proxy, no facturación de Copilot.')
    parser.add_argument('--page-size', type=int, help='Fragmentos por consulta (1–30); no modifica connection.json.')
    parser.add_argument('--replay', action='store_true', help='Volver a entregar fragmentos si se perdió contexto.')
    parser.add_argument('--out', help='Archivo nuevo; si se omite, escribe JSON en stdout.')
    args = parser.parse_args(argv)
    try:
        execute(args)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        # Never serialize headers, request objects, credentials or upstream bodies.
        message = str(error) if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError) else \
            'No se pudo leer la configuración, escribir la entrega o completar la operación; revisar archivos y permisos.'
        print(serial({'schema': SCHEMA, 'status': 'error', 'error': message}), end='', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
