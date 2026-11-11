import copy
import json
from pathlib import Path
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from brain import Budget
from context_packet import build_packet
from draft_cases import catalog, generate, markdown, verify_result, OllamaClient


def packet(text='La acción está permitida sólo con autorización vigente.'):
    class Client:
        base_url = 'http://127.0.0.1:9388'
        datasets = ['kb1']
        def retrieve(self, q):
            return [{'id': 'chunk', 'dataset_id': 'kb1', 'document_id': 'doc',
                     'document_keyword': 'Reglas.md', 'content': text}], 1
    return build_packet(Client(), 'Piloto', ['reglas'], {}, Budget(30000))[0]


TASK = {'title': 'Ensayo', 'request': 'Revisar esta regla.', 'max_cases': 1}
SELECTION = {'assessment': 'rules_found', 'rule_ids': ['E1'], 'issues': []}
DRAFT = {'cases': [{'title': 'Comprobar regla', 'preconditions': [], 'steps': ['Realizar la acción.'],
                   'expected_rule_id': 'E1', 'supporting_rule_ids': []}], 'open_questions': []}


class FakeClient:
    model = 'test-model'
    def __init__(self, answers):
        self.answers, self.requests = answers, []
    def complete(self, payload):
        self.requests.append(payload)
        return copy.deepcopy(self.answers[len(self.requests) - 1]), {'prompt_eval_count': 10, 'eval_count': 5}


class DraftTests(unittest.TestCase):
    def test_expected_and_citations_are_built_from_verified_source(self):
        p = packet()
        client = FakeClient([SELECTION, DRAFT])
        result = generate(p, TASK, client)
        case = result['cases'][0]
        self.assertEqual(case['expected'], p['passages'][0]['text'])
        evidence = case['evidence'][0]
        a, b = evidence['locator']['start_char'], evidence['locator']['end_char']
        self.assertEqual(evidence['raw_quote'], p['passages'][0]['text'][a:b])
        self.assertEqual(case['qa_review'], 'pending')
        self.assertEqual(result['semantic_validation'], 'not_performed')
        self.assertNotIn('expected', client.requests[1]['format']['properties']['cases']['items']['properties'])

    def test_table_projection_preserves_raw_offsets_and_metadata_is_not_a_rule(self):
        text = '---\ntitle: metadata\n---\n# Title\n<table>\n<tr><th>Estado</th><th>Acceso</th></tr>\n<tr><td>En espera</td><td>Sólo espera &amp; ayuda.</td></tr>\n</table>\n## Relacionado\n[[Índice]]'
        p = packet(text)
        view = catalog(p)
        self.assertEqual(len(view), 1)
        self.assertEqual(view[0]['display_text'], 'Estado: En espera | Acceso: Sólo espera & ayuda.')
        loc = view[0]['locator']
        self.assertEqual(view[0]['raw_quote'], text[loc['start_char']:loc['end_char']])
        self.assertIn('&amp;', view[0]['raw_quote'])

    def test_missing_rule_abstains_without_second_call(self):
        client = FakeClient([{'assessment': 'no_rule', 'rule_ids': [], 'issues': ['Falta confirmar el tiempo.']}])
        result = generate(packet(), TASK, client)
        self.assertEqual(result['state'], 'needs_information')
        self.assertFalse(result['cases'])
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(len(result['native_usage']), 1)

    def test_empty_context_makes_no_model_call(self):
        p = packet()
        p['passages'], p['sources'] = [], {}
        client = FakeClient([])
        result = generate(p, TASK, client)
        self.assertEqual(result['state'], 'needs_information')
        self.assertFalse(client.requests)

    def test_changed_passage_is_rejected_before_model_call(self):
        p = packet()
        p['passages'][0]['text'] = 'Una regla alterada.'
        client = FakeClient([])
        self.assertRaises(ValueError, generate, p, TASK, client)
        self.assertFalse(client.requests)

    def test_unknown_rule_and_model_expected_or_approval_cannot_be_accepted(self):
        for key, value in [('expected_rule_id', 'E99'), ('expected', 'Acceso siempre permitido.'), ('approved', True)]:
            draft = copy.deepcopy(DRAFT)
            draft['cases'][0][key] = value
            self.assertRaises(ValueError, generate, packet(), TASK, FakeClient([SELECTION, draft]))

    def test_case_count_and_empty_steps_are_rejected(self):
        draft = copy.deepcopy(DRAFT)
        draft['cases'] *= 2
        self.assertRaises(ValueError, generate, packet(), TASK, FakeClient([SELECTION, draft]))
        draft = copy.deepcopy(DRAFT)
        draft['cases'][0]['steps'] = ['']
        self.assertRaises(ValueError, generate, packet(), TASK, FakeClient([SELECTION, draft]))

    def test_supported_selection_cannot_succeed_with_no_cases(self):
        self.assertRaises(ValueError, generate, packet(), TASK,
                          FakeClient([SELECTION, {'cases': [], 'open_questions': ['Falta la UI.']}]))

    def test_result_audit_rejects_edited_expected_and_fabricated_source(self):
        p = packet()
        result = generate(p, TASK, FakeClient([SELECTION, DRAFT]))
        self.assertEqual(verify_result(p, result)['integrity'], 'ok')
        modified = copy.deepcopy(result)
        modified['cases'][0]['expected'] = 'Otro comportamiento.'
        self.assertRaises(ValueError, verify_result, p, modified)
        modified = copy.deepcopy(result)
        modified['cases'][0]['evidence'][0]['raw_quote'] = 'Texto inventado.'
        self.assertRaises(ValueError, verify_result, p, modified)
        modified = copy.deepcopy(result)
        modified['cases'] = []
        self.assertRaises(ValueError, verify_result, p, modified)

    def test_oversized_rule_is_not_silently_truncated(self):
        self.assertRaises(ValueError, catalog, packet('regla ' * 600))

    def test_markdown_preserves_qa_review_and_escapes_html(self):
        draft = copy.deepcopy(DRAFT)
        draft['cases'][0]['title'] = '<script>untrusted</script>'
        result = generate(packet(), TASK, FakeClient([SELECTION, draft]))
        rendered = markdown(result)
        self.assertIn('pendiente de revisión de QA', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)


class OllamaHTTPTests(unittest.TestCase):
    def setUp(self):
        self.responses = []
        self.requests = []
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                owner.requests.append((self.path, json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(owner.responses.pop(0)).encode())
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.client = OllamaClient('test', f'http://127.0.0.1:{server.server_port}')

    def test_local_chat_and_native_usage_without_thinking_field(self):
        self.responses = [{'done': True, 'done_reason': 'stop', 'message': {'content': '{"ok":true}', 'thinking': 'not saved'},
                           'prompt_eval_count': 4, 'eval_count': 2}]
        parsed, usage = self.client.complete({'model': 'test'})
        self.assertTrue(parsed['ok'])
        self.assertEqual(self.requests[0][0], '/api/chat')
        self.assertEqual(usage['prompt_eval_count'], 4)
        self.assertNotIn('thinking', json.dumps(usage))

    def test_truncated_or_invalid_json_never_becomes_a_draft(self):
        self.responses = [{'done': True, 'done_reason': 'length', 'message': {'content': '{}'}},
                          {'done': True, 'done_reason': 'stop', 'message': {'content': 'invalid'}}]
        self.assertRaises(ValueError, self.client.complete, {})
        self.assertRaises(ValueError, self.client.complete, {})

    def test_remote_url_requires_a_separate_integration(self):
        self.assertRaises(ValueError, OllamaClient, 'model', 'http://example.com')


if __name__ == '__main__':
    unittest.main(verbosity=2)
