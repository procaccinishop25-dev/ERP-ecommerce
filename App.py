import streamlit as st
import pandas as pd
from supabase import create_client

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📊 ERP Ecommerce")

# =========================
# 📦 VENDITE
# =========================
st.subheader("📦 Vendite")

vendite = supabase.table("Vendite").select("*").execute()

if vendite.data:
    df_vendite = pd.DataFrame(vendite.data)

    st.metric("Totale vendite", len(df_vendite))
    st.metric("Fatturato totale", df_vendite["revenue"].sum())

    st.dataframe(df_vendite)
else:
    st.warning("Nessuna vendita trovata")

# =========================
# 📦 ANAGRAFICA PRODOTTI
# =========================
st.subheader("📦 Anagrafica prodotti")

prodotti = supabase.table("Anagrafica prodotti").select("*").execute()

if prodotti.data:
    df_prodotti = pd.DataFrame(prodotti.data)

    st.metric("Totale prodotti", len(df_prodotti))

    st.dataframe(df_prodotti)
else:
    st.warning("Nessun prodotto trovato")

# =========================
# 📦 MOVIMENTO MAGAZZINO
# =========================
st.subheader("📦 Movimento magazzino")

magazzino = supabase.table("Movimento magazzino").select("*").execute()

if magazzino.data:
    df_mag = pd.DataFrame(magazzino.data)

    st.dataframe(df_mag)
else:
    st.warning("Nessun movimento trovato")
