"""Pruebas de ejemplo derivadas de segundo-cerebro/reglas.md, revisables por QA."""
import unittest
from calculadora import sumar


class PruebasCalculadora(unittest.TestCase):
    def test_suma(self):
        self.assertEqual(sumar(2, 3), 5)

    def test_identidad_cero(self):
        self.assertEqual(sumar(7, 0), 7)


if __name__ == '__main__':
    unittest.main(verbosity=2)
