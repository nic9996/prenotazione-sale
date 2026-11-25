"""Test delle funzioni di conversione degli orari."""

import unittest

from prenotazioni import minuti_in_orario, orario_in_minuti


class TestOrarioInMinuti(unittest.TestCase):
    def test_orari_validi(self):
        casi = [("00:00", 0), ("09:30", 570), ("23:59", 1439)]
        for orario, atteso in casi:
            with self.subTest(orario=orario):
                self.assertEqual(orario_in_minuti(orario), atteso)

    def test_formato_errato(self):
        for orario in ("9:30", "09.30", "0930", "09:3", "ab:cd", "", "09:30 "):
            with self.subTest(orario=orario):
                with self.assertRaises(ValueError):
                    orario_in_minuti(orario)

    def test_orario_inesistente(self):
        for orario in ("24:00", "12:60", "99:99"):
            with self.subTest(orario=orario):
                with self.assertRaises(ValueError):
                    orario_in_minuti(orario)

    def test_tipo_errato(self):
        with self.assertRaises(TypeError):
            orario_in_minuti(930)


class TestMinutiInOrario(unittest.TestCase):
    def test_valori_validi(self):
        casi = [(0, "00:00"), (570, "09:30"), (1439, "23:59")]
        for minuti, atteso in casi:
            with self.subTest(minuti=minuti):
                self.assertEqual(minuti_in_orario(minuti), atteso)

    def test_fuori_intervallo(self):
        for minuti in (-1, 1440):
            with self.subTest(minuti=minuti):
                with self.assertRaises(ValueError):
                    minuti_in_orario(minuti)

    def test_tipo_errato(self):
        with self.assertRaises(TypeError):
            minuti_in_orario("570")

    def test_conversioni_inverse(self):
        for minuti in range(0, 1440, 7):
            with self.subTest(minuti=minuti):
                self.assertEqual(orario_in_minuti(minuti_in_orario(minuti)), minuti)


if __name__ == "__main__":
    unittest.main()
