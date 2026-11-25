import unittest

from prenotazioni import Agenda, Sala, SalaNonTrovata


class TestAgenda(unittest.TestCase):
    # "aggiungi_sala" rifiuta un codice duplicato con "ValueError";
    # "sala" solleva "SalaNonTrovata" per un codice inesistente;
    def test_sale(self):
        agenda = Agenda()
        sala_a = Sala("A1", "Aula Magna", 150)
        sala_b = Sala("A1", "Sala Ricevimenti", 40)
        agenda.aggiungi_sala(sala_a)
        with self.assertRaises(ValueError):
            agenda.aggiungi_sala(sala_b)
        with self.assertRaises(SalaNonTrovata):
            agenda.sala("XXXXXX")