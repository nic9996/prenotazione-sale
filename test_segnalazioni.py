import unittest
from datetime import date

from prenotazioni import Agenda, Prenotazione, Sala


class TestSegnalazioni(unittest.TestCase):
    def test_prenotazioni_adiacenti(self):
        giorno = date(2026, 12, 1)
        oggi = date(2026, 11, 25)
        agenda = Agenda()
        sala = Sala("A2", "Aula 2", 150)
        agenda.aggiungi_sala(sala)
        prenotazione1 = Prenotazione("A2", giorno, "09:00", "10:00", "Giovanni", 60)
        agenda.prenota(prenotazione1, oggi=oggi)
        prenotazione2 = Prenotazione("A2", giorno, "10:00", "11:00", "Marco", 80)
        agenda.prenota(prenotazione2, oggi=oggi)

    def test_limite_posti(self):
        giorno = date(2026, 12, 1)
        oggi = date(2026, 11, 25)
        agenda = Agenda()
        sala = Sala("R1", "Sala Riunioni", 10)
        agenda.aggiungi_sala(sala)
        prenotazione = Prenotazione("R1", giorno, "09:00", "10:00", "Giovanni", 10)
        agenda.prenota(prenotazione, oggi=oggi)
