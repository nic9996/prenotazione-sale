# Prenotazione sale

Applicativo web per la prenotazione delle sale della sede.

- `prenotazioni.py`: motore. Sale, prenotazioni, regole della sede,
  persistenza su JSON. Le docstring ne costituiscono la specifica.
- `server.py`: interfaccia web basata sulla libreria standard.
- `modelli/`, `static/`: pagina HTML e foglio di stile.
- `dati/sale_iniziali.json`: sale della sede.

## Avvio

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

L'interfaccia è disponibile su `http://127.0.0.1:8000/`. Al primo avvio viene
creato `dati/agenda.json`, che contiene i dati di esercizio e non va
versionato.

## Convenzioni del gruppo di lavoro

### Rami

- `main` contiene sempre una versione funzionante e non riceve commit di
  sviluppo diretti.
- Ogni modifica si svolge su un ramo dedicato, creato a partire da `main`
  aggiornato:
  - `fix/<descrizione>` per le correzioni di difetti;
  - `feature/<descrizione>` per le nuove funzionalità;
  - `test/<descrizione>` per l'aggiunta di test.
- La descrizione è breve, in minuscolo, con parole separate da trattini, ad
  esempio `fix/calcolo-durata`.
- I rami si integrano in `main` con `git merge`. Dopo l'integrazione i rami
  non si cancellano.

### Commit

- Ogni commit contiene una sola modifica coerente.
- Il messaggio è in italiano, alla terza persona del presente, e descrive
  l'effetto della modifica: `Corregge il calcolo...`, `Aggiunge i test...`.
- La prima riga non supera 72 caratteri.

### Test

- I test usano `unittest` e stanno nella cartella principale, in file
  `test_*.py`.
- Si eseguono con:

  ```
  python -m unittest discover -v
  ```

- Prima di ogni merge in `main` tutti i test devono passare.
- La correzione di un difetto è preceduta da un test che lo riproduce: il
  test si registra in un commit e fallisce; la correzione si registra nel
  commit successivo e lo fa passare.

### Stile

Il codice deve superare `ruff check .` e `ruff format --check .`.
