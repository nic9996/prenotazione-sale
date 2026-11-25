import unittest
from datetime import date

from prenotazioni import Prenotazione


class TestPrenotazione(unittest.TestCase):
    def test_orari_non_ammessi(self):
         # il costruttore solleva ValueError per orari non ammessi: inizio non multiplo
        # di 30 minuti, inizio prima dell'apertura, fine dopo la chiusura, fine
        # precedente all'inizio;
        orari_non_ammessi = [
            ("07:15", "08:00"),
            ("04:00", "12:00"),
            ("12:00", "23:00"),
            ("12:00", "11:00"),
        ]
        for inizio, fine in orari_non_ammessi:
            with self.assertRaises(ValueError):
                Prenotazione("A1", date(2026, 11, 25), inizio, fine, "Apollo", 25)