import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="ERP Dashboard", layout="wide")

st.title("📊 Dashboard ERP")

# 🔐 CONNESSIONE SUPABASE
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 📦 CARICAMENTO DATI
orders = supabase.table("orders").select("*").execute().data
stock = supabase.table("stock").select("*").execute().data

df_orders = pd.DataFrame(orders)
df_stock = pd.DataFrame(stock)

# ⚠️ CONTROLLO DATI
if df_orders.empty and df_stock.empty:
    st.warning("⚠️ Nessun dato disponibile nel sistema")
    st.stop()

# 🧹 RIMOZIONE COLONNE TECNICHE
if "id" in df_orders.columns:
    df_orders = df_orders.drop(columns=["id"])

if "id" in df_stock.columns:
    df_stock = df_stock.drop(columns=["id"])

# 📊 KPI PRINCIPALI
col1, col2, col3 = st.columns(3)

col1.metric("📦 Ordini", len(df_orders))
col2.metric("🏷️ Prodotti in magazzino", len(df_stock))

fatturato = df_orders["total_amount"].sum() if "total_amount" in df_orders.columns else 0
col3.metric("💰 Fatturato totale", f"€ {fatturato}")

st.divider()

# 📦 MAGAZZINO
st.subheader("📦 Stato Magazzino")

if not df_stock.empty:
    df_stock["stato"] = df_stock.apply(
        lambda x: "🔴 BASSO" if x.get("stock_current", 0) < 5 else "🟢 OK",
        axis=1
    )

    st.dataframe(df_stock, use_container_width=True)

    # 🚨 ALERT
    st.subheader("🚨 Prodotti a rischio")

    rischio = df_stock[df_stock["stock_current"] < 5]

    if rischio.empty:
        st.success("✅ Nessun prodotto a rischio")
    else:
        st.dataframe(rischio, use_container_width=True)
else:
    st.info("Nessun dato magazzino disponibile")

# 📊 ORDINI
st.subheader("📦 Ultimi ordini")

if not df_orders.empty:
    st.dataframe(df_orders.sort_values(by="order_date", ascending=False), use_container_width=True)
else:
    st.info("Nessun ordine presente")
