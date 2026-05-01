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
    if x is None or pd.isna(x) or str(x) == "":
        return pd.Timestamp.now().date()  # 👈 FIX CRITICO
    return str(x).split(" ")[0]


# ======================
# MENU
# ======================
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Ordini", "Import"])


# ======================
# DASHBOARD
# ======================
if menu == "Dashboard":

    st.title("📊 ERP Dashboard")

    ordini = supabase.table("ordini").select("*").execute().data
    righe = supabase.table("righe_ordine").select("*").execute().data

    fatturato = sum([o.get("fatturato_totale", 0) or 0 for o in ordini])

    st.metric("Ordini", len(ordini))
    st.metric("Righe", len(righe))
    st.metric("Fatturato", f"{fatturato:.2f} €")


# ======================
# ORDINI
# ======================
if menu == "Ordini":

    st.title("📦 Ordini")
    ordini = supabase.table("ordini").select("*").execute().data
    st.dataframe(ordini)


# ======================
# IMPORT
# ======================
if menu == "Import":

    st.title("📥 Import Marketplace")

    marketplace = st.text_input("Marketplace")
    mercato = st.text_input("Mercato")

    file = st.file_uploader("Carica Excel")

    def load_parser(name):
        return importlib.import_module(f"parsers.{name}")


    if file:

        df = pd.read_excel(file)

        parser = load_parser("temu")
        df = parser.parse(df)

        st.dataframe(df.head())

        if st.button("IMPORTA"):

            try:

                # ======================
                # RIGHE TEMP
                # ======================
                righe_temp = []

                for _, r in df.iterrows():

                    prezzo = safe_float(r.get("prezzo_unitario"))
                    qty = int(safe_float(r.get("quantita")))

                    righe_temp.append({
                        "sku_prodotto": safe_str(r.get("sku_prodotto")),
                        "quantita": qty,
                        "prezzo_unitario": prezzo,
                        "totale_riga": prezzo * qty
                    })

                fatturato_totale = sum([x["totale_riga"] for x in righe_temp])

                # ======================
                # ORDINE PAYLOAD (FIX DEFINITIVO DATA)
                # ======================
                ordine_payload = {
                    "numero_ordine": safe_str(df.iloc[0].get("ordine_id")),
                    "marketplace": safe_str(marketplace),
                    "mercato": safe_str(mercato),
                    "data_ordine": safe_date(df.iloc[0].get("data_ordine")),
                    "fatturato_totale": float(fatturato_totale)
                }

                st.write("DEBUG ORDINE:", ordine_payload)

                # ======================
                # INSERT ORDINE
                # ======================
                ordine = supabase.table("ordini").insert(ordine_payload).execute()
                ordine_uuid = ordine.data[0]["id"]

                # ======================
                # RIGHE ORDINE
                # ======================
                clean_righe = []

                for r in righe_temp:
                    clean_righe.append({
                        "ordine_id": ordine_uuid,
                        "sku_prodotto": r["sku_prodotto"],
                        "quantita": r["quantita"],
                        "prezzo_unitario": r["prezzo_unitario"],
                        "totale_riga": r["totale_riga"]
                    })

                supabase.table("righe_ordine").insert(clean_righe).execute()

                st.success("IMPORT COMPLETATO 🚀")

            except Exception as e:
                st.error("❌ ERRORE COMPLETO:")
                st.exception(e)
