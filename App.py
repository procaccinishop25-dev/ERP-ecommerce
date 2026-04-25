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
    df = pd.DataFrame(magazzino.data)

    # =========================
    # 📊 STOCK PER PRODOTTO
    # =========================
    st.subheader("📊 Stock attuale per prodotto")

    stock_df = df.groupby("product_sku").apply(
        lambda x: 
        x[x["type"]=="IN"]["quantity"].sum()
        - x[x["type"]=="OUT"]["quantity"].sum()
        + x[x["type"]=="RETURN"]["quantity"].sum()
        - x[x["type"]=="LOSS"]["quantity"].sum()
    ).reset_index(name="stock")

    def status(stock):
        if stock <= 0:
            return "🔴 STOCK OUT"
        elif stock < 10:
            return "🟡 BASSO"
        else:
            return "🟢 OK"

    stock_df["status"] = stock_df["stock"].apply(status)

    st.dataframe(stock_df)

    # =========================
    # 📋 MOVIMENTI GREZZI
    # =========================
    st.subheader("📋 Storico movimenti")

    st.dataframe(df)

else:
    st.warning("Nessun movimento magazzino trovato")
