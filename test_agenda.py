import unittest
from datetime import date, timedelta

from prenotazioni import Agenda, Sala, SalaNonTrovata, Prenotazione, DataNonAmmessa, ORIZZONTE_GIORNI


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

    def test_data_non_ammessa(self):
        # "prenota" solleva "DataNonAmmessa" per una data passata, una Domenica e una
        #  data oltre l'orizzonte, e accetta la data di oggi;
        giorno1 = date(2026, 11, 24)
        giorno2 = date(2026, 11, 29)  # è una Domenica
        oggi = date(2026, 11, 25)
        agenda = Agenda()
        sala = Sala("A1", "Aula Magna", 150)
        agenda.aggiungi_sala(sala)
        # test data passata
        prenotazione = Prenotazione(
            "A1",
            giorno1,
            "09:00",
            "12:00",
            "Mariano",
            20,
        )
        with self.assertRaises(DataNonAmmessa):
            agenda.prenota(prenotazione, oggi=oggi)
        # test Domenica
        prenotazione = Prenotazione(
            "A1",
            giorno2,
            "09:00",
            "12:00",
            "Mariano",
            20,
        )
        with self.assertRaises(DataNonAmmessa):
            agenda.prenota(prenotazione, oggi=oggi)
        # test data oltre l'orizzonte
        prenotazione = Prenotazione(
            "A1",
            oggi + timedelta(days=ORIZZONTE_GIORNI + 1),
            "09:00",
            "12:00",
            "Mariano",
            20,
        )
        with self.assertRaises(DataNonAmmessa):
            agenda.prenota(prenotazione, oggi=oggi)
        # accettazione data di oggi
        prenotazione = Prenotazione("A1", oggi, "09:00", "12:00", "Mariano", 20)
        agenda.prenota(prenotazione, oggi=oggi)
        