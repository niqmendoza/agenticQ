import json
from pathlib import Path
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from ragflow_client import RAGFlowClient, RetrievalError


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.body = {'code': 0, 'data': {'total': 1, 'chunks': [{
            'id': 'c1', 'document_id': 'd1', 'document_keyword': 'Reglas.md',
            'dataset_id': 'kb1', 'content': 'Una regla.'}]}}
        self.http_code = 200
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                owner.requests.append((self.path, json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                self.send_response(owner.http_code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(owner.body).encode())
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def test_calls_only_retrieval_and_limits_scope(self):
        client = RAGFlowClient(self.url, 'test-secret', ['kb1'], page_size=3)
        chunks, total = client.retrieve('permisos')
        self.assertEqual(total, 1)
        path, payload = self.requests[0]
        self.assertEqual(path, '/api/v1/retrieval')
        self.assertEqual(payload['dataset_ids'], ['kb1'])
        self.assertEqual(payload['page_size'], 3)
        self.assertFalse(payload['keyword'])
        self.assertFalse(payload['include_knowledge_compilation'])
        self.assertNotIn('test-secret', json.dumps(chunks))

    def test_http_error_not_empty_and_no_credential_leak(self):
        self.http_code = 401
        client = RAGFlowClient(self.url, 'test-secret', ['kb1'])
        with self.assertRaises(RetrievalError) as caught:
            client.retrieve('q')
        self.assertNotIn('test-secret', str(caught.exception))
        self.assertIn('401', str(caught.exception))

    def test_application_error_not_empty(self):
        self.body = {'code': 102, 'message': 'internal-secret'}
        with self.assertRaises(RetrievalError) as caught:
            RAGFlowClient(self.url, 'secret', ['kb1']).retrieve('q')
        self.assertNotIn('internal-secret', str(caught.exception))

    def test_reject_missing_dataset_and_unsafe_url(self):
        self.assertRaises(RetrievalError, RAGFlowClient, self.url, 'secret', [])
        self.assertRaises(RetrievalError, RAGFlowClient, 'http://example.com', 'secret', ['kb1'])
        self.assertRaises(RetrievalError, RAGFlowClient, 'https://name:secret@example.com', 'secret', ['kb1'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
