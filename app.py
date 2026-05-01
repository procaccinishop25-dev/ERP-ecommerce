import streamlit as st
import pandas as pd
import importlib

from supabase_client import supabase

st.set_page_config(page_title="ERP Ecommerce", layout="wide")

# ======================
# SIDEBAR
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

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Ordini", len(ordini))
    col2.metric("🧾 Righe", len(righe))
    col3.metric("💰 Fatturato righe", sum([r.get("totale_riga", 0) or 0 for r in righe]))


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

    st.title("📥 Import Ordini")

    source = st.selectbox("Marketplace", ["temu"])
    mercato = st.selectbox("Mercato", ["IT", "DE", "FR"])

    file = st.file_uploader("Carica Excel")

    def load_parser(source):
        return importlib.import_module(f"parsers.{source}")

    if file:

        df = pd.read_excel(file)

        parser = load_parser(source)
        df = parser.parse(df)

        st.write(df.head())

        if st.button("IMPORTA"):

            for ordine_id, gruppo in df.groupby("ordine_id"):

                righe = []

                for _, r in gruppo.iterrows():

                    prezzo = float(r.get("prezzo_base", 0) or 0)
                    quantita = int(r.get("quantita", 0) or 0)

                    totale = prezzo * quantita

                    righe.append({
                        "ordine_id": str(ordine_id),
                        "sku_prodotto": str(r.get("sku", "")),
                        "quantita": quantita,
                        "prezzo_unitario": prezzo,
                        "totale_riga": totale
                    })

                supabase.table("righe_ordine").insert(righe).execute()

                supabase.table("ordini").upsert({
                    "id": str(ordine_id),
                    "marketplace": source,
                    "mercato": mercato
                }).execute()

            st.success("IMPORT COMPLETATO")
