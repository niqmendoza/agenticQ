import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'Post Harness V2' / 'scripts'))
from validar_casos import validate
from brain import Budget
from context_packet import build_packet


class Cliente:
    base_url = 'http://127.0.0.1:9388'
    datasets = ['kb1']
    def retrieve(self, question):
        return ([{'id': 'c1', 'document_id': 'd1', 'dataset_id': 'kb1', 'content': 'La acción requiere permiso vigente.'}], 1)


class Validacion(unittest.TestCase):
    def test_ragflow_valida_integridad_y_referencia(self):
        packet, _ = build_packet(Cliente(), 'Ejemplo', ['permiso'], {}, Budget(10000))
        passage = packet['passages'][0]
        cases = {'schema': 'qa-cases/1', 'cases': [{'id':'C1', 'title':'Permiso', 'steps':['Intentar'], 'expected':'Permite', 'references':[{'source':passage['source'], 'passage_id':passage['id'], 'quote':'requiere permiso vigente'}]}]}
        self.assertTrue(validate(packet, cases)['valid'])
        broken = copy.deepcopy(packet); broken['passages'][0]['text'] += ' alterado'
        with self.assertRaises(ValueError): validate(broken, cases)
        cases['cases'][0]['references'][0]['passage_id'] = 'incorrecto'
        self.assertFalse(validate(packet, cases)['valid'])
