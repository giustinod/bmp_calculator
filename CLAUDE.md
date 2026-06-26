# BMP Calculator — Contesto progetto

## Cos'è questo repository

Prototipo Streamlit del BMP Calculator, derivato dalla specifica completa in
[BMP_Calculator_Specifica.md](BMP_Calculator_Specifica.md). Mostra le pagine
principali dell'applicazione finale (login, calcolo, gestione utenti) **senza
database e senza autenticazione reale** — è una demo navigabile, non l'app di
produzione descritta nella specifica.

Deployato su Heroku: https://radiant-beyond-48979-97c810ac5553.herokuapp.com/
(app Heroku: `radiant-beyond-48979`).

## Cosa è mock e cosa è reale

| Componente | Stato nel prototipo |
|---|---|
| Login (`auth.py`) | Finto: qualsiasi username/password entra, ruolo scelto a mano nel form |
| Calcolo BMP (`calculators.py`) | Reale ma **semplificato**: usa le formule Buswell/Boyle della specifica (composizione elementare C/H/O/N), non replica la formula completa di `Web_BMP.xlsx` (che include digeribilità, COD/VSS, NDS — più articolata) |
| Griglia + CSV (`ui/grid.py`) | Reale: input via `st.data_editor` con copia/incolla da foglio di calcolo, upload CSV, validazione stretta (numero colonne, tipi compatibili) |
| Gestione utenti (`ui/admin.py`) | Mock: CRUD utenti vive solo in `st.session_state`, nessuna persistenza |
| Audit trail / log | Non implementato (richiede DB, fuori scope del prototipo) |

## Decisioni rilevanti

- **Niente PostgreSQL nel prototipo**: la specifica prevede Heroku Postgres
  (sezione 3), ma per la demo è stato deliberatamente omesso per restare
  "stateless" e a costo zero. Da aggiungere in Fase 2 dello sviluppo reale.
- **Validazione paste rigorosa**: `ui/grid.py` intercetta i casi in cui un
  blocco di testo multi-colonna finisce incollato in una sola cella (es. CSV
  copiato come testo grezzo) e lo distribuisce solo se il numero di colonne
  corrisponde esattamente allo schema della griglia; altrimenti mostra un
  errore esplicito e non applica nulla. Requisito esplicito del cliente.
- **Copia/incolla da foglio di calcolo**: funziona in Chrome/Edge. Safari ha
  limitazioni note della Clipboard API in `st.data_editor` — comportamento
  verificato e accettato, non è un bug del codice.
- **`.python-version` invece di `runtime.txt`**: Heroku ha deprecato
  `runtime.txt` (changelog 3141); usare sempre `.python-version` nei prossimi
  progetti Python su Heroku.

## Struttura

Vedi sezione 4.2 della specifica per la struttura prevista a regime. Nel
prototipo: `app.py` (entry point + routing), `auth.py` (mock), `calculators.py`
(motore di calcolo), `ui/grid.py`, `ui/results.py`, `ui/admin.py`.

## Deploy

```
git push heroku main
heroku open
```

Nessuna config var/DB da gestire per il prototipo.
