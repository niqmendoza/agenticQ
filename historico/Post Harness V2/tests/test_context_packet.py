import argparse
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from brain import Budget
from context_packet import build_packet, digest, serial
from retrieve import execute, session_lock
from verify_context import verify


def chunk(text='La acción requiere permiso vigente.', ident='c1', document='d1', dataset='kb1'):
    return {'id': ident, 'document_id': document, 'dataset_id': dataset,
            'document_keyword': 'Reglas.md', 'content': text,
            'content_ltks': 'redundant lexical representation', 'vector_similarity': 0.9}


class Client:
    base_url = 'http://127.0.0.1:9388'
    datasets = ['kb1']

    def __init__(self, records):
        self.records = records

    def retrieve(self, question):
        return self.records[question]


class PacketTests(unittest.TestCase):
    def packet(self, chunks, *, session=None, budget=None, total=None, replay=False):
        return build_packet(Client({'q': (chunks, len(chunks) if total is None else total)}),
                            'Piloto', ['q'], session or {'delivered': []},
                            budget or Budget(10000), replay=replay)

    def test_exact_text_and_verifiable_fragment_hash_without_invented_revision(self):
        text = '<table><tr><td>{} | España</td></tr></table>\nSegunda línea.'
        packet, _ = self.packet([chunk(text)])
        passage = packet['passages'][0]
        self.assertEqual(passage['text'], text)
        self.assertEqual(passage['sha256'], digest(text))
        self.assertNotIn('content_ltks', serial(packet))
        self.assertNotIn('document_revision', serial(packet))
        self.assertNotIn('start', passage)
        self.assertEqual(packet['coverage'], 'not_asserted')
        self.assertEqual(next(iter(packet['sources'].values()))['document_id'], 'd1')

    def test_dedupe_merges_query_provenance_and_replay_restores_text(self):
        client = Client({'a': ([chunk()], 1), 'b': ([chunk(), chunk()], 2)})
        packet, session = build_packet(client, 'P', ['a', 'b'], {}, Budget(10000))
        self.assertEqual(len(packet['passages']), 1)
        self.assertEqual(packet['passages'][0]['queries'], ['Q1', 'Q2'])
        self.assertEqual(packet['omitted']['duplicates'], 2)
        second, _ = self.packet([chunk()], session=session)
        self.assertEqual(second['status'], 'already_delivered')
        self.assertEqual(second['omitted']['already_delivered']['count'], 1)
        replayed, _ = self.packet([chunk()], session=session, replay=True)
        self.assertEqual(replayed['passages'][0]['text'], chunk()['content'])

    def test_changed_content_same_remote_id_is_not_hidden(self):
        first, session = self.packet([chunk()])
        second, _ = self.packet([chunk('Cambio de regla.')], session=session)
        self.assertTrue(second['passages'])
        self.assertNotEqual(first['passages'][0]['id'], second['passages'][0]['id'])

    def test_omitted_passage_is_not_marked_delivered_and_can_be_recovered(self):
        text = 'regla ' * 1000
        packet, session = self.packet([chunk(text)], budget=Budget(2000))
        self.assertEqual(packet['status'], 'budget_exhausted')
        self.assertEqual(packet['omitted']['budget']['count'], 1)
        self.assertEqual(session['delivered'], [])
        self.assertLessEqual(len(serial(packet)), 2000)
        recovered, session = self.packet([chunk(text)], session=session)
        self.assertEqual(recovered['passages'][0]['text'], text)
        self.assertEqual(len(session['delivered']), 1)

    def test_all_metadata_and_escaped_text_count_towards_limits(self):
        try:
            import tiktoken
        except ImportError:
            self.skipTest('tiktoken opcional no instalado')
        budget = Budget(4500, 1000)
        items = [chunk('"\\\n漢字 regla ' * 100, ident=str(i)) for i in range(8)]
        packet, _ = self.packet(items, budget=budget)
        chars, tokens = budget.size(packet)
        self.assertLessEqual(chars, 4500)
        self.assertLessEqual(tokens, 1000)
        self.assertGreater(packet['omitted']['budget']['count'], 0)

    def test_empty_and_unreturned_and_budget_exhausted_are_distinct(self):
        packet, _ = self.packet([])
        self.assertEqual(packet['status'], 'empty')
        packet, _ = self.packet([], total=12)
        self.assertEqual(packet['status'], 'partial')
        self.assertEqual(packet['queries'][0]['not_returned'], 12)
        packet, _ = self.packet([chunk()], total=6)
        self.assertEqual(packet['status'], 'partial')
        self.assertEqual(packet['omitted']['upstream_not_returned'], 5)

    def test_round_robin_keeps_a_later_query_in_the_budget(self):
        client = Client({'a': ([chunk('a' * 500, str(i)) for i in range(6)], 6),
                         'b': ([chunk('b' * 500, 'later')], 1)})
        packet, _ = build_packet(client, 'P', ['a', 'b'], {}, Budget(3300))
        self.assertIn('later', [p['chunk_id'] for p in packet['passages']])
        self.assertGreater(packet['omitted']['budget']['count'], 0)

    def test_no_out_of_scope_or_malformed_fragment_is_delivered(self):
        for item in [chunk(dataset='other'), chunk(text=''), {'content': 'Missing IDs'}, None]:
            with self.subTest(item=item):
                self.assertRaises(ValueError, self.packet, [item])

    def test_verifier_rejects_edited_text_and_broken_source_references(self):
        packet, _ = self.packet([chunk()])
        self.assertEqual(verify(packet)['integrity'], 'ok')
        for field, value in [('text', 'Una regla inventada.'), ('source', 'No-existe'), ('queries', ['Q99'])]:
            modified = copy.deepcopy(packet)
            modified['passages'][0][field] = value
            with self.subTest(field=field):
                self.assertRaises(ValueError, verify, modified)


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'connection.json'
        self.config.write_text(json.dumps({'base_url': 'http://127.0.0.1:9388', 'dataset_ids': ['kb1']}))
        self.args = argparse.Namespace(application='Piloto', config=str(self.config),
            credentials_file=None, query=['q'], queries_json=None, max_chars=10000,
            max_tokens=None, session=str(self.root / 'session.json'), replay=False, out=None)
        self.client = Client({'q': ([chunk()], 1)})
        self.patcher = patch('retrieve.RAGFlowClient', return_value=self.client)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_output_then_session_and_scoping(self):
        output = io.StringIO()
        packet = execute(self.args, stream=output)
        self.assertEqual(json.loads(output.getvalue()), packet)
        path = Path(self.args.session)
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(len(json.loads(path.read_text())['delivered']), 1)
        self.args.application = 'Otra'
        self.assertRaises(ValueError, execute, self.args, stream=io.StringIO())

    def test_output_failure_never_advances_session(self):
        class Broken(io.StringIO):
            def flush(self):
                raise BrokenPipeError()
        self.assertRaises(BrokenPipeError, execute, self.args, stream=Broken())
        self.assertFalse(Path(self.args.session).exists())

    def test_short_write_never_advances_session(self):
        class Short(io.StringIO):
            def write(self, value):
                return super().write(value[:5])
        self.assertRaises(OSError, execute, self.args, stream=Short())
        self.assertFalse(Path(self.args.session).exists())

    def test_api_failure_on_later_query_never_commits_partial_evidence(self):
        self.args.query = ['q', 'not_available']
        stream = io.StringIO()
        self.assertRaises(KeyError, execute, self.args, stream=stream)
        self.assertEqual(stream.getvalue(), '')
        self.assertFalse(Path(self.args.session).exists())

    def test_evidence_file_is_private_and_never_overwritten(self):
        self.args.out = str(self.root / 'packet.json')
        first = execute(self.args)
        self.assertEqual(Path(self.args.out).stat().st_mode & 0o777, 0o600)
        self.assertRaises(ValueError, execute, self.args)
        self.assertEqual(json.loads(Path(self.args.out).read_text()), first)

    def test_input_paths_cannot_be_overwritten(self):
        self.args.session = str(self.config)
        self.assertRaises(ValueError, execute, self.args)

    def test_concurrent_session_is_rejected(self):
        with session_lock(Path(self.args.session)):
            self.assertRaises(ValueError, execute, self.args, stream=io.StringIO())


if __name__ == '__main__':
    unittest.main(verbosity=2)
