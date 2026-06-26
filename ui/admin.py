"""Pagina gestione utenti (admin) - dati solo in session_state, nessun database."""

import streamlit as st


def render_admin():
    st.subheader("Gestione utenti")
    st.caption("Prototipo: le modifiche non vengono salvate, vivono solo nella sessione corrente.")

    utenti = st.session_state.utenti

    st.markdown("**Elenco utenti**")
    st.dataframe(utenti, use_container_width=True)

    with st.expander("Crea nuovo utente"):
        with st.form("crea_utente"):
            username = st.text_input("Username")
            nome = st.text_input("Nome")
            email = st.text_input("Email")
            ruolo = st.selectbox("Ruolo", ["user", "admin"])
            password_temp = st.text_input("Password temporanea", type="password")
            submitted = st.form_submit_button("Crea utente")

        if submitted:
            if not username or not password_temp:
                st.error("Username e password temporanea sono obbligatori.")
            else:
                st.session_state.utenti.append({
                    "username": username,
                    "nome": nome,
                    "email": email,
                    "ruolo": ruolo,
                    "attivo": True,
                })
                st.success(f"Utente '{username}' creato (solo in sessione).")
                st.rerun()

    with st.expander("Modifica / disattiva utente"):
        usernames = [u["username"] for u in utenti]
        if usernames:
            selezionato = st.selectbox("Seleziona utente", usernames)
            utente = next(u for u in utenti if u["username"] == selezionato)

            with st.form("modifica_utente"):
                nuovo_ruolo = st.selectbox(
                    "Ruolo", ["user", "admin"],
                    index=["user", "admin"].index(utente["ruolo"])
                )
                nuovo_stato = st.checkbox("Attivo", value=utente["attivo"])
                nuova_password = st.text_input("Reset password (lascia vuoto per non modificare)", type="password")
                salva = st.form_submit_button("Salva modifiche")

            if salva:
                utente["ruolo"] = nuovo_ruolo
                utente["attivo"] = nuovo_stato
                if nuova_password:
                    st.success(f"Password resettata per '{selezionato}' (simulata, nessun salvataggio).")
                st.success(f"Utente '{selezionato}' aggiornato (solo in sessione).")
                st.rerun()
        else:
            st.info("Nessun utente disponibile.")
