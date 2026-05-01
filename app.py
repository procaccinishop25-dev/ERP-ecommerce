import streamlit as st
import pandas as pd
import importlib
from supabase_client import supabase

st.set_page_config(page_title="ERP Ecommerce", layout="wide")


# ======================
# SAFE FUNCTIONS
# ======================
def safe_float(x):
    try:
        if x is None or pd.isna(x) or x == "":
            return 0.0
        return float(str(x).replace(",", "."))
    except:
        return 0.0


def safe_str(x):
    if x is None or pd.isna(x):
        return ""
    return str(x)


def safe_int(x):
    try:
        return int(float(x))
    except:
        return 0


def safe_date(x):
    try:
        if x is None or pd.isna(x):
            return pd.Timestamp.now().strftime("%Y-%m-%d")
        return pd.to_datetime(x).strftime("%Y-%m-%d")
    except:
        return pd.Timestamp.now().strftime("%Y-%m-%d")


# ======================
# IMPORT UI
# ======================
st.title("📥 ERP IMPORT")

marketplace = st.text_input("Marketplace")
mercato = st.text_input("Mercato")

file = st.file_uploader("Excel")


def load_parser():
    return importlib.import_module("parsers.temu")


if file:

    df = pd.read_excel(file)

    parser = load_parser()
    df = parser.parse(df)

    st.write("PREVIEW FILE")
    st.dataframe(df.head())


    if st.button("IMPORTA"):

        # ======================
        # CREA RIGHE
        # ======================
        righe_raw = []

        for _, r in df.iterrows():

            sku = safe_str(r.get("sku_prodotto"))

            if sku == "":
                continue

            prezzo = safe_float(r.get("prezzo_unitario"))
            qty = safe_int(r.get("quantita"))

            righe_raw.append({
                "sku_prodotto": sku,
                "quantita": qty,
                "prezzo_unitario": prezzo,
                "totale_riga": prezzo * qty
            })

        if len(righe_raw) == 0:
            st.error("NESSUNA RIGA VALIDA")
            st.stop()

        fatturato_totale = sum([x["totale_riga"] for x in righe_raw])

        # ======================
        # ORDINE
        # ======================
        ordine_payload = {
            "numero_ordine": safe_str(df.iloc[0].get("ordine_id")),
            "marketplace": marketplace,
            "mercato": mercato,
            "data_ordine": safe_date(df.iloc[0].get("data_ordine")),
            "fatturato_totale": float(fatturato_totale)
        }

        ordine = supabase.table("ordini").insert(ordine_payload).execute()
        ordine_id = ordine.data[0]["id"]

        # ======================
        # RIGHE (SAFE INSERT)
        # ======================
        clean_righe = []

        for r in righe_raw:

            try:
                clean_righe.append({
                    "ordine_id": ordine_id,
                    "sku_prodotto": r["sku_prodotto"],
                    "quantita": int(r["quantita"]),
                    "prezzo_unitario": float(r["prezzo_unitario"]),
                    "totale_riga": float(r["totale_riga"])
                })
            except Exception as e:
                st.warning(f"RIGA SCARTATA: {r} | {e}")

        supabase.table("righe_ordine").insert(clean_righe).execute()

        st.success("IMPORT COMPLETATO 🚀")
