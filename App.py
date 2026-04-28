import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# 🔐 CONNESSIONE SUPABASE
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 🧠 DASHBOARD
# =========================
st.title("📊 ERP Ecommerce Dashboard")

# =========================
# 📦 ORDERS
# =========================
st.subheader("📦 Ordini")

orders = supabase.table("orders").select("*").execute()

if orders.data:
    df_orders = pd.DataFrame(orders.data)

    st.metric("Totale ordini", len(df_orders))

    # sicurezza se la colonna non esiste o è vuota
    revenue = df_orders["revenue"].sum() if "revenue" in df_orders.columns else 0
    st.metric("Fatturato totale", f"€ {revenue:,.2f}")

    st.dataframe(df_orders, use_container_width=True)
else:
    st.warning("Nessun ordine trovato")

# =========================
# 📦 PRODUCTS
# =========================
st.subheader("📦 Prodotti")

products = supabase.table("products").select("*").execute()

if products.data:
    df_products = pd.DataFrame(products.data)

    st.metric("Totale prodotti", len(df_products))

    st.dataframe(df_products, use_container_width=True)
else:
    st.warning("Nessun prodotto trovato")

# =========================
# 🧱 STOCK MOVEMENTS
# =========================
st.subheader("📦 Movimenti Magazzino")

stock = supabase.table("stock_movements").select("*").execute()

if stock.data:
    df_stock = pd.DataFrame(stock.data)

    st.dataframe(df_stock, use_container_width=True)
else:
    st.warning("Nessun movimento stock trovato")
