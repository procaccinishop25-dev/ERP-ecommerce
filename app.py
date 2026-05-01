import streamlit as st
import pandas as pd
import importlib

from supabase_client import supabase

st.set_page_config(page_title="ERP Ecommerce", layout="wide")

# ======================
# MENU
# ======================
menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Ordini", "Import"]
)

# ======================
# DASHBOARD
# ======================
if menu == "Dashboard":

    st.title("📊 Dashboard")

    ordini = supabase.table("ordini").select("*").execute().data
    righe = supabase.table("righe_ordine").select("*").execute().data

    fatturato = sum([o.get("fatturato_totale", 0) or 0 for o in ordini])

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Ordini", len(ordini))
    col2.metric("🧾 Righe", len(righe))
    col3.metric("💰 Fatturato", f"{fatturato:.2f} €")


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

    st.title("📥 Import Temu")

    marketplace = st.text_input("Marketplace")
    mercato = st.text_input("Mercato")

    file = st.file_uploader("Carica Excel")

    def load_parser(source):
        return importlib.import_module(f"parsers.{source}")

    if file:

        df = pd.read_excel(file)

        parser = load_parser("temu")
        df = parser.parse(df)

        st.write(df.head())

        if st.button("IMPORTA"):

            for ordine_id, gruppo in df.groupby("ordine_id"):

                # ======================
                # RIGHE ORDINE
                # ======================
                righe = []

                for _, r in gruppo.iterrows():

                    righe.append({
                        "ordine_id": str(ordine_id),
                        "sku_prodotto": str(r["sku_prodotto"]),
                        "quantita": int(r["quantita"]),
                        "prezzo_unitario": float(r["prezzo_unitario"]),
                        "totale_riga": float(r["totale_riga"])
                    })

                supabase.table("righe_ordine").insert(righe).execute()

                # ======================
                # ORDINE (HEADER)
                # ======================
                data_ordine = gruppo.iloc[0]["data_ordine"]

                fatturato_totale = sum([x["totale_riga"] for x in righe])

                supabase.table("ordini").upsert({
                    "numero_ordine": str(ordine_id),
                    "data_ordine": str(data_ordine),
                    "marketplace": marketplace,
                    "mercato": mercato,
                    "fatturato_totale": float(fatturato_totale)
                }).execute()

            st.success("IMPORT COMPLETATO")
