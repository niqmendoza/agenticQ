"""Guard the interpretation of the new retrieval regression signals."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'ragflow-local'))
from evaluate_retrieval import check_markers, fingerprint


class RetrievalEvaluationTests(unittest.TestCase):
    def test_link_to_source_does_not_count_as_source_body(self):
        check = {'id': 'a', 'title': 'Permisos', 'document': 'Regla.md', 'contains': ['permiso vigente']}
        result = check_markers(check, [{'path': 'Indice.md', 'text': '[[Regla]] permiso vigente'}])
        self.assertFalse(result['matched'])
        self.assertFalse(result['source_present'])

    def test_source_name_without_rule_is_insufficient(self):
        check = {'id': 'a', 'title': 'Permisos', 'document': 'Regla.md', 'contains': ['permiso vigente']}
        result = check_markers(check, [{'path': 'Regla.md', 'text': '# Otros temas'}])
        self.assertFalse(result['matched'])
        self.assertTrue(result['source_present'])

    def test_empty_acl_symbol_cannot_be_normalized_away(self):
        check = {'id': 'a', 'title': 'ACL', 'document': 'Regla.md', 'contains': ['None'], 'literal': ['{}']}
        result = check_markers(check, [{'path': 'Regla.md', 'text': 'None significa público.'}])
        self.assertFalse(result['matched'])
        self.assertIn('{}', result['missing_markers'])

    def test_markup_and_accents_do_not_hide_the_same_cue(self):
        check = {'id': 'a', 'title': 'Producción', 'document': 'Regla.md', 'contains': ['detalles técnicos']}
        self.assertTrue(check_markers(check, [{'path': 'Regla.md', 'text': '**DETALLES** técnicos'}])['matched'])

    def test_stable_identity_ignores_scores_but_detects_content_changes(self):
        chunk = {'id': 'c', 'document_id': 'd', 'dataset_id': 'kb', 'content': 'Regla', 'similarity': 0.2}
        self.assertEqual(fingerprint(chunk), fingerprint({**chunk, 'similarity': 0.3}))
        self.assertNotEqual(fingerprint(chunk), fingerprint({**chunk, 'content': 'Otra regla'}))


if __name__ == '__main__':
    unittest.main(verbosity=2)
