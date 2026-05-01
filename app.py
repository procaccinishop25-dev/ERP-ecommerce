import streamlit as st
import pandas as pd

from supabase_client import supabase
from parsers import parse_temu

st.title("ERP IMPORT ORDINI")

# 1. scelta marketplace
marketplace = st.selectbox("Marketplace", ["Temu"])
mercato = st.selectbox("Mercato", ["IT", "DE", "FR"])

# 2. upload file
file = st.file_uploader("Carica file Excel")

if file:

    df = pd.read_excel(file)

    # 3. parsing
    if marketplace == "Temu":
        df = parse_temu(df)

    st.write("Preview dati:", df.head())

    # 4. bottone import
    if st.button("IMPORTA ORDINI"):

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

            # inserisci righe
            supabase.table("righe_ordine").insert(righe).execute()

            # ordine (summary)
            supabase.table("ordini").upsert({
                "id": ordine_id,
                "marketplace": marketplace,
                "mercato": mercato
            }).execute()

        st.success("IMPORT COMPLETATO")
