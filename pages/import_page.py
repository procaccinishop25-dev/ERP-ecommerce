import streamlit as st
import pandas as pd

from db import supabase
from mappings import MAPPINGS
from marketplace_rules import calcola_totale_riga


def show():
    st.title("Import Ordini")

    marketplace = st.selectbox("Marketplace", list(MAPPINGS.keys()))
    mercato = st.selectbox("Mercato", ["IT", "FR", "DE"])

    file = st.file_uploader("Carica file Excel/CSV", type=["xlsx", "csv"])

    if file:

        if file.name.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)

        st.subheader("Anteprima")
        st.dataframe(df.head())

        if st.button("IMPORTA"):

            mapping = MAPPINGS[marketplace]
            reverse_mapping = {v: k for k, v in mapping.items()}

            df = df.rename(columns=reverse_mapping)

            required = ["numero_ordine", "sku_prodotto", "quantita", "prezzo_unitario"]

            missing = [c for c in required if c not in df.columns]
            if missing:
                st.error(f"Mancano colonne: {missing}")
                st.stop()

            df["quantita"] = df["quantita"].astype(float)
            df["prezzo_unitario"] = df["prezzo_unitario"].astype(float)

            df["totale_riga"] = df.apply(
                lambda r: calcola_totale_riga(r, marketplace),
                axis=1
            )

            # =====================
            # ORDINI
            # =====================
            ordini = df.drop_duplicates(subset=["numero_ordine"])

            ordine_map = {}

            for _, row in ordini.iterrows():

                res = supabase.table("ordini").insert({
                    "numero_ordine": row["numero_ordine"],
                    "data_ordine": row.get("data_ordine"),
                    "marketplace": marketplace,
                    "mercato": mercato,
                    "fatturato_totale": df[df["numero_ordine"] == row["numero_ordine"]]["totale_riga"].sum()
                }).execute()

                ordine_map[row["numero_ordine"]] = res.data[0]["id"]

            # =====================
            # RIGHE
            # =====================
            righe = []

            for _, row in df.iterrows():
                righe.append({
                    "ordine_id": ordine_map[row["numero_ordine"]],
                    "sku_prodotto": row["sku_prodotto"],
                    "quantita": int(row["quantita"]),
                    "prezzo_unitario": float(row["prezzo_unitario"]),
                    "totale_riga": float(row["totale_riga"])
                })

            supabase.table("righe_ordine").insert(righe).execute()

            st.success("IMPORT COMPLETATO ✅")
