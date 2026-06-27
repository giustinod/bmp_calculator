# BMP Calculator — Specifica di Progettazione

**Web App per il calcolo del Potenziale di Biometano (BMP)**
Versione 1.1 — Giugno 2025

---

## 1. Descrizione del Progetto

La web app BMP Calculator è uno strumento destinato a professionisti del settore biogas/biometano per il calcolo del Potenziale di Biometano (BMP) di biomasse agricole.

Il sistema consente l'inserimento dei parametri analitici della biomassa (tramite griglia interattiva o upload CSV), applica le equazioni di Buswell/Boyle alle frazioni organiche e restituisce i valori di produzione teorica di biogas e metano per tonnellata di tal quale.

**Caratteristiche principali:**

- Accesso autenticato con gestione ruoli (admin/user)
- Input dati via griglia editabile con copia/incolla da Excel e upload CSV
- Selezione Tipologia biomassa per popolamento automatico dei coefficienti mancanti
- Output tabulare con esportazione CSV
- Tracciamento completo delle operazioni (audit trail) su database
- Pagina di amministrazione per la gestione degli utenti (ruolo admin)

---

## 2. Requisiti Funzionali

### 2.1 Autenticazione

Implementazione di un sistema di autenticazione custom basato su bcrypt e `session_state` di Streamlit, con query diretta su PostgreSQL. La libreria `streamlit-authenticator` (progettata per credenziali YAML) è stata scartata in favore di un approccio nativo al database, più pulito e manutenibile (~50 righe di codice).

| Campo | Dettaglio |
|---|---|
| Login | Username + password con hashing bcrypt |
| Sessione | Gestita tramite `st.session_state`, con logout esplicito |
| Ruoli | `admin` (calcolo + log + gestione utenti), `user` (solo calcolo) |
| Sicurezza | Credenziali DB in variabili d'ambiente (`st.secrets` / Heroku config vars) |

### 2.2 Input Dati

#### Griglia interattiva

La griglia è implementata con il componente nativo `st.data_editor` (Streamlit ≥ 1.23), in sostituzione di `st-aggrid`. La scelta elimina una dipendenza esterna fragile (`st-aggrid` è mantenuto da un singolo contributor con frequenti rotture di compatibilità) e garantisce supporto nativo al copia/incolla da Excel.

| Campo | Obbligatorietà | Note |
|---|---|---|
| Tipologia | Obbligatorio | Dropdown: Silomais, Trinciato_Mais, Siloerba, Trinciato_Erba, Silovernino, Trinciato_Vernino, Slurry |
| Alimento | Facoltativo | Nome libero, soggetto a valutazione GDPR |
| SS (%) | Obbligatorio | Sostanza secca |
| CEN.% | Obbligatorio | Ceneri |
| P.G.% | Obbligatorio | Proteina grezza |
| E.E.% | Obbligatorio | Estratto etereo (grassi) |
| NDF% | Obbligatorio | Fibra neutro detersa |
| uNDF240 | Facoltativo | Se assente, valorizzato da lookup Tipologia |
| AMIDO% | Facoltativo | |
| Prezzo/Ton | Facoltativo | Se assente, i campi €/Biogas e €/CH4 non vengono calcolati |

#### Upload CSV

Upload di file CSV con mapping automatico delle colonne e preview prima dell'elaborazione. Validazione con `pandas.to_numeric` per pulizia dati da copia/incolla.

### 2.3 Logica di Calcolo

Il calcolo è basato sulle equazioni di Buswell/Boyle per la digestione anaerobica. I coefficienti di composizione elementare (C, H, O, N) per ciascuna frazione organica sono derivati dalle formule molecolari standard (fonte: Angelidaki & Ellegaard, 2004):

| Frazione | Formula | C% | H% | O% | N% |
|---|---|---|---|---|---|
| Carboidrati / NDF / Amido | C₆H₁₀O₅ | 44.4 | 6.2 | 49.4 | 0 |
| Proteina grezza (P.G.) | C₅H₇NO₂ | 53.1 | 6.2 | 28.3 | 12.4 |
| Estratto etereo (E.E.) | C₅₇H₁₀₄O₆ | 77.4 | 11.8 | 10.9 | 0 |

Tabella di lookup uNDF240 per Tipologia:

| Tipologia | uNDF240 |
|---|---|
| Silomais | 0.75 |
| Trinciato_Mais | 0.75 |
| Siloerba | 0.65 |
| Trinciato_Erba | 0.65 |
| Silovernino | 0.65 |
| Trinciato_Vernino | 0.65 |
| Slurry | 0.30 |

### 2.4 Output

| Campo | Condizione | Descrizione |
|---|---|---|
| Biogas, NM³/Ton TQ | Sempre | Produzione specifica di biogas |
| CH4 NM³/Ton TQ | Sempre | Produzione specifica di metano |
| CH4 % | Sempre | Percentuale metano nel biogas |
| € / Biogas NM³ | Se Prezzo/Ton fornito | Costo per NM³ di biogas |
| € / CH4 NM³ | Se Prezzo/Ton fornito | Costo per NM³ di metano |

Tutti i risultati sono esportabili in formato CSV.

### 2.5 Audit Trail

Ogni operazione di calcolo viene registrata nella tabella `logs` con: utente, timestamp, input (JSON), output (JSON). L'accesso ai log è riservato al ruolo `admin`.

> **Nota GDPR:** il campo Alimento è testo libero e potrebbe contenere riferimenti a soggetti identificabili. Si raccomanda una valutazione prima del go-live.

### 2.6 Gestione Utenti (pagina admin)

Pagina riservata al ruolo `admin` per la gestione completa degli utenti dell'applicazione.

| Funzionalità | Dettaglio |
|---|---|
| Lista utenti | Tabella con username, nome, email, ruolo e stato (attivo/disattivato) |
| Creazione utente | Form con username, nome, email, ruolo e password temporanea |
| Modifica | Aggiornamento ruolo e dati anagrafici |
| Reset password | L'admin imposta una nuova password; l'utente è forzato a cambiarla al primo accesso |
| Disattivazione | Soft delete (flag `attivo = false`), senza cancellazione fisica del record |

---

## 3. Stack Tecnologico

| Componente | Tecnologia | Note |
|---|---|---|
| Framework | Python + Streamlit | |
| Griglia input | `st.data_editor` (nativo) | In sostituzione di `st-aggrid` (dipendenza fragile) |
| Autenticazione | Auth custom (bcrypt + session_state) | In sostituzione di `streamlit-authenticator` |
| Database | PostgreSQL (Heroku Postgres) | Piano Essential-0, ~$5/mese |
| Calcolo | pandas + modulo `calculators.py` | |
| Deploy | Heroku (min. 2 dyno) | 2 dyno per gestione concorrenza |
| Segreti | `st.secrets` / Heroku config vars | Nessuna credenziale in codebase |

---

## 4. Architettura dei Dati

### 4.1 Schema PostgreSQL

**Tabella `users`**

| Colonna | Tipo | Vincoli | Descrizione |
|---|---|---|---|
| id | SERIAL | PK | |
| username | VARCHAR(80) | UNIQUE NOT NULL | |
| password_hash | TEXT | NOT NULL | bcrypt hash |
| nome | VARCHAR(120) | | |
| email | VARCHAR(200) | UNIQUE | |
| ruolo | VARCHAR(20) | DEFAULT 'user' | `'admin'` \| `'user'` |
| attivo | BOOLEAN | DEFAULT TRUE | Soft delete flag |
| forza_cambio_pw | BOOLEAN | DEFAULT FALSE | Reset password flag |

**Tabella `logs`**

| Colonna | Tipo | Vincoli | Descrizione |
|---|---|---|---|
| id | SERIAL | PK | |
| user_id | INTEGER | FK → users.id | |
| timestamp | TIMESTAMPTZ | DEFAULT NOW() | |
| input_data | JSONB | | Array di righe input |
| output_data | JSONB | | Array di risultati corrispondenti |

### 4.2 Struttura del Progetto

| File / Directory | Responsabilità |
|---|---|
| `app.py` | Entry point Streamlit, routing pagine |
| `calculators.py` | Motore di calcolo BMP (formule Buswell/Boyle, lookup uNDF240) |
| `auth.py` | Login, logout, verifica ruolo, cambio password forzato |
| `db.py` | Connection pool psycopg2, query su `users` e `logs` |
| `ui/grid.py` | Componente griglia `st.data_editor` |
| `ui/results.py` | Tabella output, metriche, export CSV |
| `ui/admin.py` | Pagina gestione utenti (CRUD, reset password) |
| `.streamlit/secrets.toml` | Credenziali locali (non in codebase, solo sviluppo) |
| `requirements.txt` | pandas, psycopg2-binary, bcrypt, streamlit |
| `Procfile` | `web: streamlit run app.py --server.port=$PORT` |
| `tests/` | Test unitari pytest per `calculators.py` e `auth.py` |

---

## 5. Stima dei Tempi

La stima copre sviluppo, test e deploy. Unità: ore effettive di lavoro. Tariffa: **€40/ora** (collaborazione B2B).

### Fase 1 — Setup + Motore di calcolo

| Attività | Ore |
|---|---|
| Setup progetto (struttura, venv, requirements.txt) | 1 |
| `calculators.py` — implementazione formule Buswell/BMP | 4 |
| Logica lookup uNDF240 per Tipologia | 1 |
| Validazione input (campi obbligatori, pulizia, range) | 2 |
| Test unitari (pytest, valori attesi da xlsx come fixture) | 3 |
| **Subtotale Fase 1** | **11** |

### Fase 2 — Integrazione DB + Autenticazione

| Attività | Ore |
|---|---|
| DDL PostgreSQL (tabelle `users`, `logs`) + seed utenti di test | 1.5 |
| Layer connessione DB (psycopg2 + connection pool) | 1.5 |
| Auth custom (bcrypt, login form, session_state, logout, cambio password forzato) | 3 |
| Audit trail (serializzazione input/output JSON su `logs`) | 2 |
| Test (flusso auth, scrittura log, gestione errori DB) | 3 |
| **Subtotale Fase 2** | **11** |

### Fase 3 — UI Streamlit

| Attività | Ore |
|---|---|
| Struttura app (pagine, sidebar, navigazione) | 1.5 |
| Dropdown Tipologia + auto-populate coefficienti mancanti | 1.5 |
| `st.data_editor` (≥10 righe, copia/incolla da Excel) | 3 |
| Upload CSV (parsing, mapping colonne, preview) | 2 |
| Sezione risultati (tabella output, metriche aggregate) | 1.5 |
| Export CSV risultati | 1 |
| Test funzionale UI (flussi completi, edge cases) | 4 |
| **Subtotale Fase 3** | **14.5** |

### Fase 4 — Deploy Heroku

| Attività | Ore |
|---|---|
| Configurazione app (Procfile, runtime.txt, buildpack Python) | 1 |
| Provisioning Heroku Postgres + apply schema DDL | 1 |
| Config vars / `st.secrets` per credenziali e DB URL | 0.5 |
| Smoke test post-deploy (auth, calcolo, log, export) | 2 |
| **Subtotale Fase 4** | **4.5** |

### Fase 5 — Pagina Gestione Utenti (admin)

| Attività | Ore |
|---|---|
| Lista utenti con ruolo e stato | 1.5 |
| Form creazione nuovo utente | 2 |
| Modifica ruolo e dati anagrafici | 1 |
| Reset password con cambio forzato al primo accesso | 1.5 |
| Disattivazione utente (soft delete) | 0.5 |
| Test (flussi CRUD, permessi, edge cases) | 2 |
| **Subtotale Fase 5** | **8.5** |

### Riepilogo sviluppo

| Fase | Ore | Importo |
|---|---|---|
| 1 — Motore di calcolo | 11 | € 440 |
| 2 — DB + Autenticazione | 11 | € 440 |
| 3 — UI Streamlit | 14.5 | € 580 |
| 4 — Deploy Heroku | 4.5 | € 180 |
| 5 — Gestione Utenti | 8.5 | € 340 |
| **Totale sviluppo** | **49.5** | **€ 1.980** |

In giornate effettive da 6 ore: circa **8 giorni lavorativi**.

---

## 6. Preventivo Economico

### Voce una tantum

| Descrizione | Importo |
|---|---|
| Sviluppo e deploy dell'applicazione completa (49.5h × €40) | **€ 1.980** |

### Canone annuale

| Descrizione | Importo |
|---|---|
| Manutenzione, aggiornamenti e supporto (1.5h/mese media, fatturabili trimestralmente) | **€ 720/anno** |

Il canone copre: aggiornamenti dipendenze (Streamlit, psycopg2, bcrypt), correzioni bug, monitoraggio Heroku e piccole richieste operative. Si rinnova tacitamente salvo disdetta con 30 giorni di preavviso.

### Totale primo anno

| Voce | Importo |
|---|---|
| Sviluppo | € 1.980 |
| Canone annuale | € 720 |
| **Totale primo anno** | **€ 2.700** |

---

## 7. Note di Sicurezza e Rischi

### 7.1 Sicurezza

- Nessuna credenziale in codebase: uso esclusivo di `st.secrets` in sviluppo e Heroku config vars in produzione
- Password hashing con bcrypt
- Input sanitizzato con `pandas.to_numeric` prima dell'elaborazione
- Accesso ai log e alla gestione utenti riservato al ruolo `admin`

### 7.2 Rischi e Mitigazioni

| Rischio | Probabilità | Mitigazione |
|---|---|---|
| Scarto formule BMP vs xlsx originale | Media | Sessione di calibrazione con dati Silomais (fixture pytest) prima di chiudere Fase 1 |
| Heroku Postgres richiede carta di credito | Alta | Verificare account Heroku configurato prima di iniziare Fase 4 |
| Concorrenza con singolo dyno | Bassa | Configurare almeno 2 dyno in produzione |
| GDPR su campo Alimento | Media | Valutare anonimizzazione o policy di retention sui log prima del go-live |

### 7.3 Roadmap post-MVP

- Valutare migrazione a st-oauth (Google/GitHub) per eliminare la gestione password
- Aggiungere paginazione e filtri sulla vista log per l'admin
- Considerare Heroku Scheduler per archiviazione periodica dei log

### 7.4 Situazione attuale

**Heroku (heroku remote)** → deploy live: https://radiant-beyond-48979-97c810ac5553.herokuapp.com/
**GitHub (origin remote)** → https://github.com/giustinod/bmp_calculator → backup/storico del codice, con LICENSE e CLAUDE.md inclusi
**CLAUDE.md** → contesto persistente per future sessioni (cosa è mock, decisioni prese, note su Safari/paste, ecc.)

Struttura del progetto a posto. Prossimi push: ricordati di spingere su entrambi i remote (git push origin main e git push heroku main) quando fai modifiche.