"""Autenticazione finta per il prototipo: nessun database, nessuna verifica reale."""

import streamlit as st

UTENTI_DEMO = [
    {"username": "admin", "nome": "Amministratore Demo", "email": "admin@example.com", "ruolo": "admin", "attivo": True},
    {"username": "operatore", "nome": "Operatore Demo", "email": "operatore@example.com", "ruolo": "user", "attivo": True},
]


def init_session_state():
    if "auth_utente" not in st.session_state:
        st.session_state.auth_utente = None
    if "utenti" not in st.session_state:
        st.session_state.utenti = [dict(u) for u in UTENTI_DEMO]


def is_logged_in() -> bool:
    return st.session_state.get("auth_utente") is not None


def utente_corrente() -> dict | None:
    return st.session_state.get("auth_utente")


def is_admin() -> bool:
    utente = utente_corrente()
    return bool(utente and utente.get("ruolo") == "admin")


def login_form():
    st.title("BMP Calculator — Login")
    st.caption("Prototipo dimostrativo — qualsiasi combinazione di credenziali consente l'accesso.")

    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="demo")
        ruolo = st.selectbox("Ruolo (solo per simulazione prototipo)", ["admin", "user"])
        submitted = st.form_submit_button("Accedi")

    if submitted:
        if not username or not password:
            st.error("Inserire username e password.")
            return
        st.session_state.auth_utente = {
            "username": username,
            "nome": username.capitalize(),
            "ruolo": ruolo,
        }
        st.rerun()


def logout():
    st.session_state.auth_utente = None
    st.rerun()
