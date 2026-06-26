"""Motore di calcolo BMP (Buswell/Boyle) - versione prototipo, nessuna persistenza."""

import pandas as pd

# Composizione elementare frazioni organiche (Angelidaki & Ellegaard, 2004)
# C%, H%, O%, N% sul peso della frazione
COMPOSIZIONE = {
    "carboidrati": {"C": 44.4, "H": 6.2, "O": 49.4, "N": 0.0},   # NDF / Amido
    "proteina": {"C": 53.1, "H": 6.2, "O": 28.3, "N": 12.4},     # P.G.
    "lipidi": {"C": 77.4, "H": 11.8, "O": 10.9, "N": 0.0},       # E.E.
}

UNDF240_LOOKUP = {
    "Silomais": 0.75,
    "Trinciato_Mais": 0.75,
    "Siloerba": 0.65,
    "Trinciato_Erba": 0.65,
    "Silovernino": 0.65,
    "Trinciato_Vernino": 0.65,
    "Slurry": 0.30,
}

TIPOLOGIE = list(UNDF240_LOOKUP.keys())

CAMPI_OBBLIGATORI = ["Tipologia", "SS", "CEN", "PG", "EE", "NDF"]


def applica_default_undf240(riga: dict) -> dict:
    """Se uNDF240 assente, lo valorizza da lookup Tipologia."""
    riga = dict(riga)
    if riga.get("uNDF240") in (None, "", 0) or pd.isna(riga.get("uNDF240")):
        riga["uNDF240"] = UNDF240_LOOKUP.get(riga.get("Tipologia"))
    return riga


def valida_riga(riga: dict) -> list[str]:
    """Ritorna la lista di errori di validazione per una riga (vuota se ok)."""
    errori = []
    for campo in CAMPI_OBBLIGATORI:
        valore = riga.get(campo)
        if valore in (None, "") or (isinstance(valore, float) and pd.isna(valore)):
            errori.append(f"Campo obbligatorio mancante: {campo}")
    return errori


def calcola_bmp(riga: dict) -> dict:
    """Applica Buswell/Boyle a una riga di input e ritorna i risultati.

    Formula semplificata a fini prototipali: composizione elementare pesata
    sulle frazioni organiche (NDF, P.G., E.E.), stechiometria di Buswell per
    %CH4, e una stima di biogas specifico per tonnellata di tal quale basata
    su sostanza secca e digeribilità approssimata da uNDF240.
    """
    riga = applica_default_undf240(riga)

    ss = float(riga["SS"])
    cen = float(riga["CEN"])
    pg = float(riga["PG"])
    ee = float(riga["EE"])
    ndf = float(riga["NDF"])
    amido = float(riga.get("AMIDO") or 0)
    undf240 = float(riga.get("uNDF240") or 0)

    # Frazione di NDF effettivamente digeribile (resto è fibra indigeribile)
    ndf_digeribile = ndf * (1 - undf240)

    # Composizione elementare pesata (C/H/O/N) sulle frazioni digeribili
    frazioni = {
        "proteina": pg,
        "lipidi": ee,
        "carboidrati": ndf_digeribile + amido,
    }
    totale_frazioni = sum(frazioni.values()) or 1.0

    c = sum(frazioni[f] * COMPOSIZIONE[f]["C"] for f in frazioni) / 100
    h = sum(frazioni[f] * COMPOSIZIONE[f]["H"] for f in frazioni) / 100
    o = sum(frazioni[f] * COMPOSIZIONE[f]["O"] for f in frazioni) / 100
    n = sum(frazioni[f] * COMPOSIZIONE[f]["N"] for f in frazioni) / 100

    # Coefficienti stechiometrici di Buswell (mol CO2-eq / mol CH4-eq)
    coeff_co2 = c / 2 + h / 8 - o / 4 - 3 * n / 8
    coeff_ch4 = c / 2 - h / 8 + o / 4 + 3 * n / 8

    denom = coeff_co2 + coeff_ch4
    ch4_pct = (coeff_ch4 / denom * 100) if denom > 0 else 0.0

    # Biogas specifico per tonnellata di tal quale (stima su SS e sostanza organica digeribile)
    sostanza_organica = ss * (100 - cen) / 100
    biogas_nm3 = sostanza_organica * totale_frazioni / 100 * 4.0  # fattore di conversione empirico

    ch4_nm3 = biogas_nm3 * ch4_pct / 100

    risultato = {
        "Biogas_NM3_Ton_TQ": round(biogas_nm3, 2),
        "CH4_NM3_Ton_TQ": round(ch4_nm3, 2),
        "CH4_pct": round(ch4_pct, 1),
    }

    prezzo = riga.get("Prezzo_Ton")
    if prezzo not in (None, "", 0) and not (isinstance(prezzo, float) and pd.isna(prezzo)):
        prezzo = float(prezzo)
        risultato["Euro_per_Biogas_NM3"] = round(prezzo / biogas_nm3, 4) if biogas_nm3 else None
        risultato["Euro_per_CH4_NM3"] = round(prezzo / ch4_nm3, 4) if ch4_nm3 else None
    else:
        risultato["Euro_per_Biogas_NM3"] = None
        risultato["Euro_per_CH4_NM3"] = None

    return risultato


def calcola_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Calcola BMP per ogni riga di un DataFrame di input, ritorna DataFrame con risultati e errori."""
    righe_out = []
    for _, riga in df.iterrows():
        riga_dict = riga.to_dict()
        errori = valida_riga(riga_dict)
        if errori:
            righe_out.append({**riga_dict, "Errori": "; ".join(errori)})
            continue
        risultati = calcola_bmp(riga_dict)
        righe_out.append({**riga_dict, **risultati, "Errori": ""})
    return pd.DataFrame(righe_out)
