import streamlit as st
import pandas as pd
import importlib
from supabase_client import supabase


def safe_float(x):
    try:
        if x is None:
            return 0.0
        return float(str(x).replace(",", "."))
    except:
        return 0.0


st.title("ERP IMPORT")

marketplace = st.text_input("Marketplace")
mercato = st.text_input("Mercato")

file = st.file_uploader("File Excel")

def load_parser(name):
    return importlib.import_module(f"parsers.{name}")


if file:

    df = pd.read_excel(file)

    parser = load_parser("temu")  # poi diventa dinamico
    df = parser.parse(df)

    st.write(df.head())

    if st.button("IMPORTA"):

        # ======================
        # 1. CREA ORDINE HEADER
        # ======================
        ordine_id_esterno = str(df.iloc[0]["ordine_id"])
        data_ordine = df.iloc[0]["data_ordine"]

        righe_temp = []

        for _, r in df.iterrows():

            prezzo = safe_float(r.get("prezzo_unitario", 0))
            qty = int(safe_float(r.get("quantita", 0)))

            righe_temp.append({
                "sku_prodotto": str(r.get("sku_prodotto", "")),
                "quantita": qty,
                "prezzo_unitario": prezzo,
                "totale_riga": prezzo * qty
            })

        fatturato_totale = sum([x["totale_riga"] for x in righe_temp])

        ordine = supabase.table("ordini").insert({
            "numero_ordine": ordine_id_esterno,
            "marketplace": marketplace,
            "mercato": mercato,
            "data_ordine": data_ordine,
            "fatturato_totale": fatturato_totale
        }).execute()

        ordine_uuid = ordine.data[0]["id"]

        # ======================
        # 2. INSERISCI RIGHE
        # ======================
        for r in righe_temp:
            r["ordine_id"] = ordine_uuid

        supabase.table("righe_ordine").insert(righe_temp).execute()

        st.success("IMPORT COMPLETATO")
