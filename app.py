import streamlit as st
import pandas as pd
import importlib

from supabase_client import supabase


def load_parser(source):
    return importlib.import_module(f"parsers.{source}")


st.title("ERP IMPORT")

# marketplace dinamico
source = st.selectbox("Marketplace", ["temu", "amazon", "shopify"])
mercato = st.selectbox("Mercato", ["IT", "DE", "FR"])

file = st.file_uploader("Carica Excel")

if file:

    df = pd.read_excel(file)

    parser = load_parser(source)
    df = parser.parse(df)

    st.write(df.head())

    if st.button("IMPORTA"):

        for ordine_id, gruppo in df.groupby("ordine_id"):

            righe = []

            for _, r in gruppo.iterrows():

                totale = (
                    r["prezzo_base"] +
                    r["spedizione"] +
                    r["imposta_articolo"] +
                    r["imposta_spedizione"]
                )

                righe.append({
                    "ordine_id": ordine_id,
                    "sku": r["sku"],
                    "quantita": r["quantita"],
                    "prezzo_base": r["prezzo_base"],
                    "spedizione": r["spedizione"],
                    "imposta_articolo": r["imposta_articolo"],
                    "imposta_spedizione": r["imposta_spedizione"],
                    "totale_riga": totale
                })

            supabase.table("righe_ordine").insert(righe).execute()

            supabase.table("ordini").upsert({
                "id": ordine_id,
                "marketplace": source,
                "mercato": mercato
            }).execute()

        st.success("IMPORT COMPLETATO")
