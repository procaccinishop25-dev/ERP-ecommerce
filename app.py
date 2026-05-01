import streamlit as st
import pandas as pd
import importlib
from supabase_client import supabase

st.set_page_config(page_title="ERP", layout="wide")


# =====================
# FUNZIONI SICURE
# =====================
def safe_float(x):
    try:
        if x is None or pd.isna(x):
            return 0.0
        return float(str(x).replace(",", "."))
    except:
        return 0.0


def safe_str(x):
    if x is None or pd.isna(x):
        return ""
    return str(x)


def safe_date(x):
    if x is None or pd.isna(x):
        return pd.Timestamp.now().strftime("%Y-%m-%d")
    return pd.to_datetime(x).strftime("%Y-%m-%d")


# =====================
# IMPORT
# =====================
st.title("📥 Import Ordini")

marketplace = st.text_input("Marketplace")
mercato = st.text_input("Mercato")

file = st.file_uploader("Excel")

def load_parser():
    return importlib.import_module("parsers.temu")


if file:

    df = pd.read_excel(file)
    parser = load_parser()
    df = parser.parse(df)

    st.write(df.head())

    if st.button("IMPORTA"):

        # =====================
        # RIGHE
        # =====================
        righe = []

        for _, r in df.iterrows():

            prezzo = safe_float(r.get("prezzo_unitario"))
            qty = int(safe_float(r.get("quantita")))

            righe.append({
                "sku_prodotto": safe_str(r.get("sku_prodotto")),
                "quantita": qty,
                "prezzo_unitario": prezzo,
                "totale_riga": prezzo * qty
            })

        # 🔥 FATTURATO CORRETTO (NON PIÙ 0)
        fatturato_totale = sum([x["totale_riga"] for x in righe])

        # =====================
        # ORDINE
        # =====================
        ordine_payload = {
            "numero_ordine": safe_str(df.iloc[0]["ordine_id"]),
            "marketplace": marketplace,
            "mercato": mercato,
            "data_ordine": safe_date(df.iloc[0].get("data_ordine")),
            "fatturato_totale": fatturato_totale
        }

        ordine = supabase.table("ordini").insert(ordine_payload).execute()
        ordine_id = ordine.data[0]["id"]

        # =====================
        # RIGHE ORDINE
        # =====================
        for r in righe:
            r["ordine_id"] = ordine_id

        supabase.table("righe_ordine").insert(righe).execute()

        st.success("IMPORT COMPLETATO")
