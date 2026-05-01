import streamlit as st
import pandas as pd
import importlib
from supabase_client import supabase

st.set_page_config(page_title="ERP Ecommerce", layout="wide")


# ======================
# SAFE CONVERSION
# ======================
def safe_float(x):
    try:
        if x is None:
            return 0.0
        return float(str(x).replace(",", "."))
    except:
        return 0.0


# ======================
# SIDEBAR MENU
# ======================
menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Ordini", "Import"]
)


# ======================
# DASHBOARD
# ======================
if menu == "Dashboard":

    st.title("📊 Dashboard ERP")

    ordini = supabase.table("ordini").select("*").execute().data
    righe = supabase.table("righe_ordine").select("*").execute().data

    fatturato = sum([o.get("fatturato_totale", 0) or 0 for o in ordini])

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Ordini", len(ordini))
    col2.metric("🧾 Righe Ordine", len(righe))
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

    st.title("📥 Import Marketplace")

    marketplace = st.text_input("Marketplace (temu, amazon, shopify...)")
    mercato = st.text_input("Mercato (IT, DE, FR...)")

    file = st.file_uploader("Carica file Excel")

    # carica parser dinamico
    def load_parser(name):
        return importlib.import_module(f"parsers.{name}")


    if file:

        df = pd.read_excel(file)

        parser = load_parser("temu")  # puoi renderlo dinamico dopo
        df = parser.parse(df)

        st.write("Anteprima dati:")
        st.dataframe(df.head())

        if st.button("IMPORTA"):

            # =========================
            # CREA ORDINE (HEADER)
            # =========================
            ordine_esterno = str(df.iloc[0]["ordine_id"])
            data_ordine = df.iloc[0].get("data_ordine", None)

            righe_temp = []

            # =========================
            # CREA RIGHE
            # =========================
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

            # =========================
            # INSERT ORDINE (UUID ERP)
            # =========================
            ordine = supabase.table("ordini").insert({
                "numero_ordine": ordine_esterno,
                "marketplace": marketplace,
                "mercato": mercato,
                "data_ordine": data_ordine,
                "fatturato_totale": fatturato_totale
            }).execute()

            ordine_uuid = ordine.data[0]["id"]

            # =========================
            # INSERT RIGHE
            # =========================
            for r in righe_temp:
                r["ordine_id"] = ordine_uuid

            supabase.table("righe_ordine").insert(righe_temp).execute()

            st.success("IMPORT COMPLETATO CON SUCCESSO 🚀")
