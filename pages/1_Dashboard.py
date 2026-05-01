import streamlit as st
import pandas as pd
from supabase import create_client

st.title("📊 Dashboard ERP")

# 🔐 Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 📦 DATI
orders = supabase.table("orders").select("*").execute().data
stock = supabase.table("stock").select("*").execute().data

df_orders = pd.DataFrame(orders)
df_stock = pd.DataFrame(stock)

# ⚠️ controllo dati
if df_orders.empty or df_stock.empty:
    st.warning("⚠️ Dati insufficienti per visualizzare la dashboard")
    st.stop()

# 📊 KPI PRINCIPALI
col1, col2, col3 = st.columns(3)

col1.metric("📦 Ordini", len(df_orders))
col2.metric("🏷️ Prodotti in magazzino", len(df_stock))
col3.metric(
    "💰 Fatturato totale",
    f"€ {df_orders['total_amount'].sum() if 'total_amount' in df_orders else 0}"
)

st.divider()

# 📦 MAGAZZINO
st.subheader("📦 Stato Magazzino")

df_stock["stato"] = df_stock.apply(
    lambda x: "🔴 BASSO" if x["stock_current"] < 5 else "🟢 OK",
    axis=1
)

st.dataframe(df_stock, use_container_width=True)

# 🚨 PRODOTTI A RISCHIO
st.subheader("🚨 Prodotti a rischio di esaurimento")

rischio = df_stock[df_stock["stock_current"] < 5]

if rischio.empty:
    st.success("✅ Nessun prodotto a rischio")
else:
    st.dataframe(rischio, use_container_width=True)
