import streamlit as st
import pandas as pd
import importlib
from supabase_client import supabase

st.set_page_config(page_title="ERP Ecommerce", layout="wide")


# =========================
# SAFE PARSING
# =========================
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
    try:
        if x is None or pd.isna(x):
            return pd.Timestamp.now().strftime("%Y-%m-%d")
        return pd.to_datetime(x).strftime("%Y-%m-%d")
    except:
        return pd.Timestamp.now().strftime("%Y-%m-%d")


# =========================
# UI
# =========================
st.sidebar.title("ERP MENU")
menu = st.sidebar.radio("Vai a:", ["Import", "Ordini", "Dashboard"])


# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":

    st.title("📊 Dashboard ERP")

    ordini = supabase.table("ordini").select("*").execute().data
    righe = supabase.table("righe_ordine").select("*").execute().data

    fatturato = sum([o.get("fatturato_totale", 0) or 0 for o in ordini])

    col1, col2, col3 = st.columns(3)
    col1.metric("Ordini", len(ordini))
    col2.metric("Righe", len(righe))
    col3.metric("Fatturato", f"{fatturato:.2f} €")


# =========================
# ORDINI
# =========================
if menu == "Ordini":

    st.title("📦 Ordini")

    ordini = supabase.table("ordini").select("*").execute().data
    st.dataframe(ordini)


# =========================
# IMPORT
# =========================
if menu == "Import":

    st.title("📥 Import Ordini Marketplace")

    marketplace = st.text_input("Marketplace")
    mercato = st.text_input("Mercato")

    file = st.file_uploader("Carica Excel")

    def load_parser():
        return importlib.import_module("parsers.temu")


    if file:

        df = pd.read_excel(file)
        parser = load_parser()
        df = parser.parse(df)

        st.write("Preview:")
        st.dataframe(df.head())

        if st.button("IMPORTA"):

            # =====================
            # RIGHE ORDINE
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

            # =====================
            # FATTURATO ORDINE
            # =====================
            fatturato_totale = sum([x["totale_riga"] for x in righe])

            # =====================
            # ORDINE HEADER
            # =====================
            ordine_payload = {
                "numero_ordine": safe_str(df.iloc[0].get("ordine_id")),
                "marketplace": marketplace,
                "mercato": mercato,
                "data_ordine": safe_date(df.iloc[0].get("data_ordine")),
                "fatturato_totale": fatturato_totale
            }

            ordine = supabase.table("ordini").insert(ordine_payload).execute()
            ordine_id = ordine.data[0]["id"]

            # =====================
            # RIGHE + FK
            # =====================
            for r in righe:
                r["ordine_id"] = ordine_id

            supabase.table("righe_ordine").insert(righe).execute()

            st.success("IMPORT COMPLETATO 🚀")
