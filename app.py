"""BMP Calculator - Prototipo dimostrativo.

Mostra le pagine principali dell'applicazione (login, calcolo, gestione utenti)
senza alcuna connessione a database: autenticazione finta, calcolo in memoria,
nessun audit trail persistito. Pensato per essere deployato su Heroku come demo.
"""

import streamlit as st

from auth import init_session_state, is_logged_in, is_admin, utente_corrente, login_form, logout
from ui.grid import render_griglia
from ui.results import render_risultati
from ui.admin import render_admin

st.set_page_config(page_title="BMP Calculator - Prototipo", page_icon="🌱", layout="wide")

init_session_state()

if not is_logged_in():
    login_form()
    st.stop()

utente = utente_corrente()

with st.sidebar:
    st.markdown(f"**Utente:** {utente['nome']}")
    st.markdown(f"**Ruolo:** {utente['ruolo']}")
    st.divider()
    pagine = ["Calcolo BMP"]
    if is_admin():
        pagine.append("Gestione utenti")
    pagina = st.radio("Navigazione", pagine)
    st.divider()
    if st.button("Logout"):
        logout()

st.title("🌱 BMP Calculator")
st.caption("Prototipo dimostrativo — nessun dato viene salvato su database.")

if pagina == "Calcolo BMP":
    df_input = render_griglia()
    st.divider()
    render_risultati(df_input)
elif pagina == "Gestione utenti":
    render_admin()
