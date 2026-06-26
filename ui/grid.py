"""Componente griglia input: st.data_editor + upload CSV. Nessuna persistenza."""

import pandas as pd
import streamlit as st

from calculators import TIPOLOGIE

COLONNE = [
    "Tipologia", "Alimento", "SS", "CEN", "PG", "EE", "NDF",
    "uNDF240", "AMIDO", "Prezzo_Ton",
]

COLONNE_NUMERICHE = [c for c in COLONNE if c not in ("Tipologia", "Alimento")]

ETICHETTE = {
    "Tipologia": "Tipologia",
    "Alimento": "Alimento",
    "SS": "SS (%)",
    "CEN": "CEN.%",
    "PG": "P.G.%",
    "EE": "E.E.%",
    "NDF": "NDF%",
    "uNDF240": "uNDF240",
    "AMIDO": "AMIDO%",
    "Prezzo_Ton": "Prezzo/Ton",
}


def dataframe_vuoto(n_righe: int = 10) -> pd.DataFrame:
    df = pd.DataFrame({col: [None] * n_righe for col in COLONNE})
    return df


def _split_testo_incollato(testo: str) -> list[list[str]]:
    """Divide un blocco di testo incollato in righe/colonne (tab o virgola come separatore)."""
    righe = testo.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    righe = [r for r in righe if r != ""]
    if not righe:
        return []
    delimitatore = "\t" if "\t" in righe[0] else ","
    return [r.split(delimitatore) for r in righe]


def _valida_e_convalida_valore(colonna: str, valore: str):
    """Valida un singolo valore testuale rispetto al tipo atteso dalla colonna."""
    valore = valore.strip()
    if valore == "":
        return True, None
    if colonna == "Tipologia":
        return (valore in TIPOLOGIE), valore
    if colonna == "Alimento":
        return True, valore
    try:
        return True, float(valore.replace(",", "."))
    except ValueError:
        return False, valore


def _correggi_paste_anomalo(df_nuovo: pd.DataFrame, df_precedente: pd.DataFrame):
    """Rileva incolla multi-colonna finiti in una sola cella (testo grezzo con virgole/tab/newline),
    li ridistribuisce sulla griglia se il numero di colonne è compatibile, altrimenti segnala errore
    e ripristina il valore precedente, senza applicare dati incompatibili."""
    df_out = df_nuovo.copy()
    errori: list[str] = []
    n_colonne_attese = len(COLONNE)

    for idx in list(df_out.index):
        for col in COLONNE:
            valore = df_out.at[idx, col]
            if not isinstance(valore, str):
                continue
            if not any(sep in valore for sep in (",", "\t", "\n")):
                continue

            righe_parse = _split_testo_incollato(valore)
            col_idx_partenza = COLONNE.index(col)
            n_col_da_partenza = n_colonne_attese - col_idx_partenza

            righe_compatibili = righe_parse and all(
                len(r) in (n_colonne_attese, n_col_da_partenza) for r in righe_parse
            )

            valore_precedente = df_precedente.at[idx, col] if idx in df_precedente.index else None
            df_out.at[idx, col] = valore_precedente

            if not righe_compatibili:
                n_trovate = len(righe_parse[0]) if righe_parse else 0
                errori.append(
                    f"Riga {idx + 1}, colonna '{ETICHETTE[col]}': il testo incollato ha {n_trovate} colonne, "
                    f"la griglia ne richiede {n_colonne_attese} (o {n_col_da_partenza} a partire da questa colonna). "
                    "Incolla dati con lo stesso numero di colonne della griglia, oppure usa la tab 'Upload CSV'."
                )
                continue

            colonne_target = (
                COLONNE[col_idx_partenza:] if len(righe_parse[0]) == n_col_da_partenza else COLONNE
            )

            for offset, riga_valori in enumerate(righe_parse):
                riga_idx = idx + offset
                if riga_idx not in df_out.index:
                    df_out.loc[riga_idx] = [None] * len(COLONNE)

                valori_convertiti = {}
                riga_valida = True
                for c, v in zip(colonne_target, riga_valori):
                    ok, v_conv = _valida_e_convalida_valore(c, v)
                    if not ok:
                        errori.append(
                            f"Riga {riga_idx + 1}, colonna '{ETICHETTE[c]}': valore '{v}' non compatibile "
                            "con il tipo di dato richiesto da questa colonna."
                        )
                        riga_valida = False
                        break
                    valori_convertiti[c] = v_conv

                if riga_valida:
                    for c, v in valori_convertiti.items():
                        df_out.at[riga_idx, c] = v

    return df_out, errori


def render_griglia() -> pd.DataFrame:
    st.subheader("Input dati biomassa")

    tab_griglia, tab_csv = st.tabs(["Griglia interattiva", "Upload CSV"])

    if "dati_input" not in st.session_state:
        st.session_state.dati_input = dataframe_vuoto()

    with tab_griglia:
        st.caption(
            "Compila la griglia manualmente, oppure seleziona una cella e incolla (Cmd+V) dati copiati "
            "da un foglio di calcolo (Excel, Numbers, Google Sheets). Il blocco incollato deve avere lo "
            "stesso numero di colonne della griglia (o a partire dalla colonna selezionata)."
        )
        df_precedente = st.session_state.dati_input.copy()

        df_modificato = st.data_editor(
            df_precedente,
            num_rows="dynamic",
            column_config={
                "Tipologia": st.column_config.SelectboxColumn(
                    ETICHETTE["Tipologia"], options=TIPOLOGIE, required=False
                ),
                **{
                    col: st.column_config.TextColumn(ETICHETTE[col])
                    for col in ["Alimento"]
                },
                **{
                    col: st.column_config.NumberColumn(ETICHETTE[col])
                    for col in COLONNE_NUMERICHE
                },
            },
            use_container_width=True,
            key="editor_griglia",
        )

        df_corretto, errori_paste = _correggi_paste_anomalo(df_modificato, df_precedente)
        if errori_paste:
            for errore in errori_paste:
                st.error(errore)

        st.session_state.dati_input = df_corretto

    with tab_csv:
        st.caption("Carica un file CSV con intestazioni corrispondenti ai campi richiesti.")
        file_csv = st.file_uploader("Seleziona file CSV", type=["csv"])
        if file_csv is not None:
            try:
                df_csv = pd.read_csv(file_csv)
            except Exception as exc:
                st.error(f"Errore lettura CSV: {exc}")
                df_csv = None

            if df_csv is not None:
                colonne_mancanti = [c for c in COLONNE if c not in df_csv.columns]
                colonne_estranee = [c for c in df_csv.columns if c not in COLONNE]

                if colonne_mancanti or colonne_estranee:
                    st.error(
                        f"Il CSV non corrisponde allo schema della griglia ({len(COLONNE)} colonne attese: "
                        f"{', '.join(COLONNE)}). "
                        + (f"Colonne mancanti: {', '.join(colonne_mancanti)}. " if colonne_mancanti else "")
                        + (f"Colonne non riconosciute: {', '.join(colonne_estranee)}." if colonne_estranee else "")
                    )
                else:
                    st.markdown("**Anteprima dati caricati**")
                    st.dataframe(df_csv.head(20), use_container_width=True)

                    df_csv_validato = df_csv.copy()
                    errori_csv = []
                    for col in COLONNE_NUMERICHE:
                        convertiti = pd.to_numeric(df_csv_validato[col], errors="coerce")
                        non_convertibili = df_csv_validato[col].notna() & convertiti.isna()
                        for riga_idx in df_csv_validato.index[non_convertibili]:
                            errori_csv.append(
                                f"Riga {riga_idx + 1}, colonna '{ETICHETTE[col]}': valore "
                                f"'{df_csv_validato.at[riga_idx, col]}' non è un numero valido."
                            )
                        df_csv_validato[col] = convertiti

                    tipologie_non_valide = ~df_csv_validato["Tipologia"].isin(TIPOLOGIE) & df_csv_validato["Tipologia"].notna()
                    for riga_idx in df_csv_validato.index[tipologie_non_valide]:
                        errori_csv.append(
                            f"Riga {riga_idx + 1}, colonna 'Tipologia': valore "
                            f"'{df_csv_validato.at[riga_idx, 'Tipologia']}' non è una tipologia valida."
                        )

                    if errori_csv:
                        st.warning("Il CSV contiene valori non compatibili (le righe interessate non verranno importate):")
                        for errore in errori_csv:
                            st.write(f"- {errore}")

                    if st.button("Usa questi dati nella griglia"):
                        st.session_state.dati_input = df_csv_validato[COLONNE].reset_index(drop=True)
                        st.success("Dati importati nella griglia interattiva.")
                        st.rerun()

    return st.session_state.dati_input
