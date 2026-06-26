"""Tabella output, metriche aggregate ed export CSV."""

import pandas as pd
import streamlit as st

from calculators import calcola_dataframe


def render_risultati(df_input: pd.DataFrame):
    st.subheader("Risultati")

    df_valido = df_input.dropna(how="all")
    if df_valido.empty:
        st.info("Inserisci almeno una riga di dati per calcolare i risultati.")
        return

    if st.button("Calcola BMP", type="primary"):
        df_risultati = calcola_dataframe(df_valido)
        st.session_state.df_risultati = df_risultati

    df_risultati = st.session_state.get("df_risultati")
    if df_risultati is None:
        return

    errori = df_risultati[df_risultati["Errori"] != ""]
    if not errori.empty:
        st.warning(f"{len(errori)} riga/righe con errori di validazione (vedi colonna Errori).")

    st.dataframe(df_risultati, use_container_width=True)

    df_ok = df_risultati[df_risultati["Errori"] == ""]
    if not df_ok.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Biogas medio (NM³/Ton TQ)", f"{df_ok['Biogas_NM3_Ton_TQ'].mean():.1f}")
        col2.metric("CH4 medio (NM³/Ton TQ)", f"{df_ok['CH4_NM3_Ton_TQ'].mean():.1f}")
        col3.metric("CH4 % medio", f"{df_ok['CH4_pct'].mean():.1f}%")

    csv = df_risultati.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Esporta risultati in CSV",
        data=csv,
        file_name="bmp_risultati.csv",
        mime="text/csv",
    )
