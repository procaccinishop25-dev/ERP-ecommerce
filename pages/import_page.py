import streamlit as st
import pandas as pd
from db import supabase

def show():
    st.title("Import Ordini")

    file = st.file_uploader("Carica file Temu", type=["xlsx", "csv"])

    if file:
        # Legge file
        if file.name.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)

        st.write("Anteprima:")
        st.dataframe(df.head())

        if st.button("IMPORTA"):
            
            # PRENDI SOLO LE COLONNE BASE
            df = df.rename(columns={
                "ID Ordine": "numero_ordine",
                "Codice SKU": "sku_prodotto",
                "quantità acquistata": "quantita",
                "prezzo base della merce": "prezzo_unitario"
            })

            # Rimuove righe vuote
            df = df.dropna(subset=["numero_ordine"])

            # Calcolo
            df["totale_riga"] = df["quantita"] * df["prezzo_unitario"]

            # =====================
            # INSERT ORDINI
            # =====================
            ordini_unici = df.drop_duplicates(subset=["numero_ordine"])

            ordine_id_map = {}

            for _, row in ordini_unici.iterrows():
                res = supabase.table("ordini").insert({
                    "numero_ordine": row["numero_ordine"],
                    "marketplace": "TEMU",
                    "mercato": "IT",
                    "fatturato_totale": row["totale_riga"]
                }).execute()

                ordine_id_map[row["numero_ordine"]] = res.data[0]["id"]

            # =====================
            # INSERT RIGHE
            # =====================
            righe = []

            for _, row in df.iterrows():
                righe.append({
                    "ordine_id": ordine_id_map[row["numero_ordine"]],
                    "sku_prodotto": row["sku_prodotto"],
                    "quantita": int(row["quantita"]),
                    "prezzo_unitario": float(row["prezzo_unitario"]),
                    "totale_riga": float(row["totale_riga"])
                })

            supabase.table("righe_ordine").insert(righe).execute()

            st.success("IMPORT COMPLETATO ✅")
