"""Motore di prenotazione delle sale della sede.

Le docstring descrivono il comportamento richiesto e costituiscono la
specifica del modulo.
"""

import json
from datetime import date, timedelta

# Regole della sede. Il codice deve usare queste costanti, non i valori scritti
# direttamente: se la sede cambia orario, si modifica solo qui.
APERTURA = "08:00"
CHIUSURA = "20:00"
PASSO_MINUTI = 30
ORIZZONTE_GIORNI = 60
# Giorno di chiusura, con la numerazione di date.weekday():
# 0 = lunedì, 1 = martedì, ..., 6 = domenica.
GIORNO_CHIUSURA = 6  # domenica


# ---------------------------------------------------------------------------
# Eccezioni (già complete)
# ---------------------------------------------------------------------------


class ErroreAgenda(Exception):
    """Classe base per le richieste rifiutate dall'agenda."""


class SalaNonTrovata(ErroreAgenda):
    """Il codice sala non corrisponde ad alcuna sala registrata."""


class PrenotazioneNonTrovata(ErroreAgenda):
    """L'identificativo non corrisponde ad alcuna prenotazione."""


class DataNonAmmessa(ErroreAgenda):
    """La data non è prenotabile secondo le regole della sede."""


class CapienzaInsufficiente(ErroreAgenda):
    """I partecipanti superano la capienza della sala."""


class ConflittoOrario(ErroreAgenda):
    """La richiesta si sovrappone a una prenotazione esistente."""


# ---------------------------------------------------------------------------
# Funzioni di utilità sugli orari
# ---------------------------------------------------------------------------


def orario_in_minuti(orario):
    """Converte un orario "HH:MM" nel numero di minuti dalla mezzanotte.

    Esempio: "09:30" -> 570.

    Il formato è rigido: esattamente 5 caratteri, due cifre, il carattere ":",
    due cifre. Ore tra 00 e 23, minuti tra 00 e 59.

    Solleva:
        TypeError: se `orario` non è una stringa.
        ValueError: se il formato non è rispettato o l'orario non esiste
            (es. "9:30", "09.30", "24:00", "12:60").
    """
    if not isinstance(orario, str):
        raise TypeError("L'orario deve essere una stringa nel formato HH:MM")
    if len(orario) != 5 or orario[2] != ":":
        raise ValueError(f"Orario non valido: '{orario}' (formato atteso HH:MM)")
    ore_testo, minuti_testo = orario[:2], orario[3:]
    if not (ore_testo.isdigit() and minuti_testo.isdigit()):
        raise ValueError(f"Orario non valido: '{orario}' (formato atteso HH:MM)")
    ore, minuti = int(ore_testo), int(minuti_testo)
    if ore > 23 or minuti > 59:
        raise ValueError(f"Orario inesistente: '{orario}'")
    return ore * 60 + minuti


def minuti_in_orario(minuti):
    """Converte i minuti dalla mezzanotte nella stringa "HH:MM".

    Esempio: 570 -> "09:30". Ore e minuti hanno sempre due cifre.

    Solleva:
        TypeError: se `minuti` non è un intero.
        ValueError: se `minuti` non è compreso tra 0 e 1439.
    """
    if not isinstance(minuti, int) or isinstance(minuti, bool):
        raise TypeError("I minuti devono essere un numero intero")
    if not 0 <= minuti <= 1439:
        raise ValueError(f"Minuti fuori intervallo: {minuti} (ammessi 0-1439)")
    return f"{minuti // 60:02d}:{minuti % 60:02d}"


# ---------------------------------------------------------------------------
# Sala
# ---------------------------------------------------------------------------


class Sala:
    """Una sala prenotabile della sede.

    Attributi pubblici:
        codice (str): identificativo univoco, es. "A1".
        nome (str): nome leggibile, es. "Aula Magna".
        capienza (int): numero massimo di persone.
        dotazioni (list[str]): attrezzature presenti, es. ["proiettore"].
    """

    def __init__(self, codice, nome, capienza, dotazioni=None):
        """Crea una sala validando i dati.

        - `codice` e `nome` vengono privati degli spazi iniziali e finali
          (strip) e non possono risultare vuoti.
        - `capienza` deve essere un intero maggiore o uguale a 1.
        - `dotazioni` è facoltativo (None equivale a lista vuota); ogni voce
          viene memorizzata con strip() e in minuscolo, nell'ordine dato.
          La lista memorizzata è una copia: modificare quella passata non
          deve modificare la sala.

        Solleva:
            ValueError: codice o nome vuoti, capienza minore di 1.
            TypeError: capienza non intera.
        """
        if not isinstance(codice, str) or not codice.strip():
            raise ValueError("Il codice della sala non può essere vuoto")
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Il nome della sala non può essere vuoto")
        if not isinstance(capienza, int) or isinstance(capienza, bool):
            raise TypeError("La capienza deve essere un numero intero")
        if capienza < 1:
            raise ValueError("La capienza deve essere almeno 1")
        self.codice = codice.strip()
        self.nome = nome.strip()
        self.capienza = capienza
        if dotazioni is None:
            dotazioni = []
        self.dotazioni = [d.strip().lower() for d in dotazioni]

    def ha_dotazioni(self, richieste):
        """Restituisce True se la sala dispone di TUTTE le dotazioni richieste.

        Il confronto ignora maiuscole/minuscole e spazi esterni.
        Una lista di richieste vuota restituisce True.
        """
        return all(r.strip().lower() in self.dotazioni for r in richieste)

    def to_dict(self):
        """Restituisce un dizionario con le chiavi
        "codice", "nome", "capienza", "dotazioni".
        """
        return {
            "codice": self.codice,
            "nome": self.nome,
            "capienza": self.capienza,
            "dotazioni": list(self.dotazioni),
        }

    @classmethod
    def from_dict(cls, dati):
        """Costruttore alternativo: crea una Sala dal dizionario prodotto da
        to_dict(). La chiave "dotazioni" è facoltativa.
        """
        return cls(
            dati["codice"],
            dati["nome"],
            dati["capienza"],
            dati.get("dotazioni", []),
        )

    def __str__(self):
        """Formato esatto: "A1 - Aula Magna (60 posti)"."""
        return f"{self.codice} - {self.nome} ({self.capienza} posti)"


# ---------------------------------------------------------------------------
# Prenotazione
# ---------------------------------------------------------------------------


class Prenotazione:
    """Una richiesta di utilizzo di una sala in un giorno e in una fascia oraria.

    Attributi pubblici:
        id (int | None): assegnato dall'Agenda; None finché non registrata.
        sala_codice (str)
        giorno (datetime.date)
        inizio (str): "HH:MM"
        fine (str): "HH:MM"
        referente (str): chi ha prenotato.
        partecipanti (int)
        motivo (str): descrizione libera, può essere vuota.
    """

    def __init__(
        self, sala_codice, giorno, inizio, fine, referente, partecipanti, motivo=""
    ):
        """Crea una prenotazione validando i dati che dipendono solo da essa.

        Non verifica l'esistenza della sala, la capienza, i conflitti o le
        regole sulle date: questi controlli spettano ad Agenda.prenota().

        Regole:
        - `sala_codice`, `referente`, `motivo`: si applica strip();
          sala_codice e referente non possono risultare vuoti.
        - `giorno` deve essere un oggetto datetime.date.
        - `inizio` e `fine` devono essere orari validi (vedi orario_in_minuti),
          con minuti multipli di PASSO_MINUTI, inizio >= APERTURA,
          fine <= CHIUSURA, inizio strettamente precedente a fine.
        - `partecipanti` deve essere un intero maggiore o uguale a 1.
        - `id` vale None.

        Solleva:
            TypeError: giorno non di tipo date, partecipanti non intero.
            ValueError: ogni altra violazione delle regole.
        """
        if not isinstance(sala_codice, str) or not sala_codice.strip():
            raise ValueError("Il codice della sala non può essere vuoto")
        if not isinstance(giorno, date):
            raise TypeError("Il giorno deve essere un oggetto datetime.date")

        minuto_inizio = orario_in_minuti(inizio)
        minuto_fine = orario_in_minuti(fine)
        for minuto, testo in ((minuto_inizio, inizio), (minuto_fine, fine)):
            if minuto % PASSO_MINUTI != 0:
                raise ValueError(
                    f"L'orario {testo} non è multiplo di {PASSO_MINUTI} minuti"
                )
        if minuto_inizio < orario_in_minuti(APERTURA):
            raise ValueError(f"La sede apre alle {APERTURA}")
        if minuto_fine > orario_in_minuti(CHIUSURA):
            raise ValueError(f"La sede chiude alle {CHIUSURA}")
        if minuto_inizio >= minuto_fine:
            raise ValueError("L'orario di inizio deve precedere quello di fine")

        if not isinstance(referente, str) or not referente.strip():
            raise ValueError("Il referente non può essere vuoto")
        if not isinstance(partecipanti, int) or isinstance(partecipanti, bool):
            raise TypeError("Il numero di partecipanti deve essere un intero")
        if partecipanti < 1:
            raise ValueError("Serve almeno un partecipante")

        self.id = None
        self.sala_codice = sala_codice.strip()
        self.giorno = giorno
        self.inizio = inizio
        self.fine = fine
        self.referente = referente.strip()
        self.partecipanti = partecipanti
        self.motivo = motivo.strip()

    def intervallo_minuti(self):
        """Restituisce la tupla (minuto_inizio, minuto_fine).

        Esempio: 09:00-10:30 -> (540, 630).
        """
        return orario_in_minuti(self.inizio), orario_in_minuti(self.fine)

    def durata_minuti(self):
        """Restituisce la durata in minuti. Esempio: 09:00-10:30 -> 90."""
        inizio, fine = self.intervallo_minuti()
        return fine - inizio

    def si_sovrappone(self, altra):
        """True se `altra` riguarda la stessa sala, lo stesso giorno e un
        intervallo che ha almeno un minuto in comune con questo.

        Due prenotazioni contigue (09:00-10:00 e 10:00-11:00) NON si
        sovrappongono.
        """
        if self.sala_codice != altra.sala_codice or self.giorno != altra.giorno:
            return False
        inizio_a, fine_a = self.intervallo_minuti()
        inizio_b, fine_b = altra.intervallo_minuti()
        return inizio_a <= fine_b and inizio_b <= fine_a

    def to_dict(self):
        """Restituisce un dizionario con le chiavi:
        "id", "sala", "giorno", "inizio", "fine", "referente",
        "partecipanti", "motivo".
        Il giorno è una stringa ISO ("2026-11-03").
        """
        return {
            "id": self.id,
            "sala": self.sala_codice,
            "giorno": self.giorno.isoformat(),
            "inizio": self.inizio,
            "fine": self.fine,
            "referente": self.referente,
            "partecipanti": self.partecipanti,
            "motivo": self.motivo,
        }

    @classmethod
    def from_dict(cls, dati):
        """Costruttore alternativo, inverso di to_dict().

        Ripristina anche l'id. Le chiavi "id" e "motivo" sono facoltative.
        """
        prenotazione = cls(
            dati["sala"],
            date.fromisoformat(dati["giorno"]),
            dati["inizio"],
            dati["fine"],
            dati["referente"],
            dati["partecipanti"],
            dati.get("motivo", ""),
        )
        prenotazione.id = dati.get("id")
        return prenotazione

    def __str__(self):
        """Formato esatto:
        "3 | A1 | 2026-11-03 09:00-10:30 | Mario Rossi (12 pers.)"
        Se l'id è None, al posto del numero compare "-".
        """
        identificativo = "-" if self.id is None else self.id
        return (
            f"{identificativo} | {self.sala_codice} | "
            f"{self.giorno.isoformat()} {self.inizio}-{self.fine} | "
            f"{self.referente} ({self.partecipanti} pers.)"
        )


# ---------------------------------------------------------------------------
# Agenda
# ---------------------------------------------------------------------------


class Agenda:
    """Registro delle sale e delle prenotazioni della sede.

    Attributi pubblici:
        sale (dict[str, Sala]): sale indicizzate per codice.
        prenotazioni (dict[int, Prenotazione]): prenotazioni indicizzate per id.
    """

    def __init__(self):
        """Crea un'agenda vuota. Il primo id assegnato sarà 1."""
        self.sale = {}
        self.prenotazioni = {}
        self._prossimo_id = 1

    # --- sale --------------------------------------------------------------

    def aggiungi_sala(self, sala):
        """Registra una sala.

        Solleva:
            ValueError: se esiste già una sala con lo stesso codice.
        """
        if sala.codice in self.sale:
            raise ValueError(f"Esiste già una sala con codice {sala.codice}")
        self.sale[sala.codice] = sala

    def sala(self, codice):
        """Restituisce la sala con il codice dato.

        Solleva:
            SalaNonTrovata: se il codice non è registrato.
        """
        if codice not in self.sale:
            raise SalaNonTrovata(f"La sala {codice} non esiste")
        return self.sale[codice]

    def elenco_sale(self):
        """Restituisce la lista delle sale ordinata per codice."""
        return [self.sale[codice] for codice in sorted(self.sale)]

    # --- prenotazioni ------------------------------------------------------

    def _verifica_data(self, giorno, oggi):
        """Solleva DataNonAmmessa se `giorno` non è prenotabile rispetto a `oggi`."""
        if giorno < oggi:
            raise DataNonAmmessa("Non si può prenotare una data già trascorsa")
        if giorno.weekday() == GIORNO_CHIUSURA:
            raise DataNonAmmessa("La sede è chiusa la domenica")
        if giorno > oggi + timedelta(days=ORIZZONTE_GIORNI):
            raise DataNonAmmessa(
                f"Si può prenotare al massimo {ORIZZONTE_GIORNI} giorni in anticipo"
            )

    def prenota(self, prenotazione, oggi=None):
        """Registra una prenotazione e ne restituisce l'id.

        `oggi` è la data di riferimento per i controlli sulle date; se None si
        usa date.today(). (Il parametro esiste per rendere il metodo
        verificabile con i test indipendentemente dal giorno di esecuzione.)

        I controlli si eseguono in QUESTO ORDINE e si interrompono al primo
        fallimento; una richiesta rifiutata non modifica l'agenda.
          1. la prenotazione ha già un id          -> ValueError
          2. la sala non esiste                    -> SalaNonTrovata
          3. il giorno è precedente a oggi,
             oppure è il giorno di chiusura (GIORNO_CHIUSURA),
             oppure è oltre oggi + ORIZZONTE_GIORNI -> DataNonAmmessa
             (oggi e oggi + ORIZZONTE_GIORNI sono ammessi; si controlla
             solo la data, non l'ora)
          4. partecipanti > capienza della sala    -> CapienzaInsufficiente
          5. sovrapposizione con una prenotazione
             esistente                             -> ConflittoOrario

        Se la richiesta è accettata, le viene assegnato l'id progressivo
        successivo (1, 2, 3, ...). Gli id di prenotazioni cancellate non
        vengono riutilizzati.

        Il messaggio di ogni eccezione deve spiegare il motivo in italiano:
        viene mostrato dall'interfaccia web a chi la usa.
        """
        if oggi is None:
            oggi = date.today()
        if prenotazione.id is not None:
            raise ValueError("La prenotazione è già registrata")
        sala = self.sala(prenotazione.sala_codice)
        self._verifica_data(prenotazione.giorno, oggi)
        if prenotazione.partecipanti >= sala.capienza:
            raise CapienzaInsufficiente(
                f"La sala {sala.codice} ospita al massimo {sala.capienza} persone"
            )
        for esistente in self.prenotazioni.values():
            if prenotazione.si_sovrappone(esistente):
                raise ConflittoOrario(
                    f"La sala {sala.codice} è già occupata dalle "
                    f"{esistente.inizio} alle {esistente.fine}"
                )
        prenotazione.id = self._prossimo_id
        self._prossimo_id += 1
        self.prenotazioni[prenotazione.id] = prenotazione
        return prenotazione.id

    def prenotazione(self, id_prenotazione):
        """Restituisce la prenotazione con l'id dato.

        Solleva:
            PrenotazioneNonTrovata: se l'id non esiste.
        """
        if id_prenotazione not in self.prenotazioni:
            raise PrenotazioneNonTrovata(
                f"Nessuna prenotazione con identificativo {id_prenotazione}"
            )
        return self.prenotazioni[id_prenotazione]

    def cancella(self, id_prenotazione):
        """Rimuove la prenotazione e la restituisce.

        Solleva:
            PrenotazioneNonTrovata: se l'id non esiste.
        """
        prenotazione = self.prenotazione(id_prenotazione)
        del self.prenotazioni[id_prenotazione]
        return prenotazione

    def prenotazioni_del_giorno(self, giorno, sala_codice=None):
        """Restituisce la lista delle prenotazioni del giorno dato.

        Se `sala_codice` è indicato, solo quelle della sala.
        Ordinamento: per orario di inizio, a parità per codice sala.

        Solleva:
            SalaNonTrovata: se `sala_codice` è indicato ma non esiste.
        """
        if sala_codice is not None:
            self.sala(sala_codice)
        risultato = [
            p
            for p in self.prenotazioni.values()
            if p.giorno == giorno
            and (sala_codice is None or p.sala_codice == sala_codice)
        ]
        risultato.sort(key=lambda p: (orario_in_minuti(p.inizio), p.sala_codice))
        return risultato

    def prenotazioni_della_settimana(self, giorno, sala_codice=None):
        """Restituisce le prenotazioni della settimana che contiene `giorno`.

        La settimana va dal lunedì alla domenica: se `giorno` è una domenica,
        è quella che termina con essa. Il risultato è un dizionario con 6
        chiavi di tipo date, una per ogni giorno della settimana escluso il
        giorno di chiusura (GIORNO_CHIUSURA), in ordine di data; ogni valore
        è la lista restituita da prenotazioni_del_giorno() per quel giorno
        (anche vuota).

        Solleva:
            SalaNonTrovata: se `sala_codice` è indicato ma non esiste.
        """
        lunedi = giorno - timedelta(days=giorno.weekday())
        settimana = {}
        for scarto in range(7):
            corrente = lunedi + timedelta(days=scarto)
            if corrente.weekday() != GIORNO_CHIUSURA:
                settimana[corrente] = self.prenotazioni_del_giorno(
                    corrente, sala_codice
                )
        return settimana

    def sale_libere(self, giorno, inizio, fine, persone=1, dotazioni=None, oggi=None):
        """Restituisce le sale prenotabili per la fascia indicata.

        Una sala è inclusa se ha capienza >= `persone`, dispone di tutte le
        `dotazioni` richieste (None equivale a nessuna) e non ha prenotazioni
        sovrapposte alla fascia inizio-fine del giorno indicato.

        Ordinamento: per capienza crescente, a parità per codice.
        Se il giorno non è ammesso dalle regole sulle date (vedi prenota),
        restituisce una lista vuota.

        Solleva:
            TypeError, ValueError: alle stesse condizioni di Prenotazione
                per giorno, inizio e fine; ValueError se persone < 1.
        """
        if oggi is None:
            oggi = date.today()
        if dotazioni is None:
            dotazioni = []
        if not isinstance(persone, int) or isinstance(persone, bool):
            raise TypeError("Il numero di persone deve essere un intero")
        if persone < 1:
            raise ValueError("Serve almeno una persona")
        # La prenotazione di prova valida giorno e orari prima di ogni altra cosa.
        prova = Prenotazione("-", giorno, inizio, fine, "ricerca", 1)
        try:
            self._verifica_data(giorno, oggi)
        except DataNonAmmessa:
            return []
        libere = []
        for sala in self.elenco_sale():
            if sala.capienza < persone or not sala.ha_dotazioni(dotazioni):
                continue
            prova.sala_codice = sala.codice
            occupata = any(prova.si_sovrappone(p) for p in self.prenotazioni.values())
            if not occupata:
                libere.append(sala)
        libere.sort(key=lambda s: (s.capienza, s.codice))
        return libere

    def minuti_occupati(self, sala_codice, giorno):
        """Restituisce il totale dei minuti prenotati per la sala nel giorno.

        Solleva:
            SalaNonTrovata: se la sala non esiste.
        """
        return sum(
            p.durata_minuti() for p in self.prenotazioni_del_giorno(giorno, sala_codice)
        )

    # --- persistenza -------------------------------------------------------

    def salva(self, percorso):
        """Salva l'agenda in un file JSON (UTF-8) con questa struttura:

        {
          "sale": [ <Sala.to_dict()>, ... ],
          "prenotazioni": [ <Prenotazione.to_dict()>, ... ],
          "prossimo_id": <int>
        }
        """
        dati = {
            "sale": [s.to_dict() for s in self.elenco_sale()],
            "prenotazioni": [
                self.prenotazioni[i].to_dict() for i in sorted(self.prenotazioni)
            ],
            "prossimo_id": self._prossimo_id,
        }
        with open(percorso, "w", encoding="utf-8") as f:
            json.dump(dati, f, indent=2, ensure_ascii=False)

    @classmethod
    def carica(cls, percorso):
        """Costruttore alternativo: ricostruisce un'agenda dal file JSON
        prodotto da salva().

        Le prenotazioni caricate non sono sottoposte alle regole sulle date
        (un archivio contiene legittimamente prenotazioni passate).
        Dopo il caricamento, il prossimo id assegnato deve essere quello
        salvato.

        Solleva:
            FileNotFoundError: se il file non esiste.
        """
        with open(percorso, encoding="utf-8") as f:
            dati = json.load(f)
        agenda = cls()
        for dati_sala in dati["sale"]:
            agenda.aggiungi_sala(Sala.from_dict(dati_sala))
        for dati_prenotazione in dati["prenotazioni"]:
            prenotazione = Prenotazione.from_dict(dati_prenotazione)
            agenda.prenotazioni[prenotazione.id] = prenotazione
        agenda._prossimo_id = dati["prossimo_id"]
        return agenda
