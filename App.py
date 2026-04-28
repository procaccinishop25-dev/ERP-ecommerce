import streamlit as st
import pandas as pd
from supabase import create_client

SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "LA_TUA_ANON_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📊 ERP Ecommerce Dashboard")

# =====================
# ORDERS
# =====================
st.subheader("📦 Ordini")

orders = supabase.table("orders").select("*").execute()

if orders.data:
    df_orders = pd.DataFrame(orders.data)

    st.metric("Ordini totali", len(df_orders))

    # revenue calcolata da order_items
    items = supabase.table("order_items").select("*").execute()
    df_items = pd.DataFrame(items.data)

    if not df_items.empty:
        revenue = (df_items["sale_price"] * df_items["quantity"]).sum()
    else:
        revenue = 0

    st.metric("Fatturato stimato", revenue)

    st.dataframe(df_orders)
else:
    st.warning("Nessun ordine trovato")

# =====================
# PRODUCTS
# =====================
st.subheader("📦 Prodotti")

products = supabase.table("products").select("*").execute()
variants = supabase.table("product_variants").select("*").execute()

df_products = pd.DataFrame(products.data)
df_variants = pd.DataFrame(variants.data)

st.metric("Prodotti", len(df_products))
st.metric("Varianti", len(df_variants))

st.dataframe(df_products)

# =====================
# STOCK
# =====================
st.subheader("📦 Stock attuale")

stock = supabase.table("stock_current").select("*").execute()

if stock.data:
    df_stock = pd.DataFrame(stock.data)
    st.dataframe(df_stock)
else:
    st.warning("Nessuno stock trovato")

# =====================
# FINANCE SIMPLE
# =====================
st.subheader("💰 KPI veloci")

if not df_items.empty:
    avg_price = df_items["sale_price"].mean()
    st.metric("Prezzo medio vendita", round(avg_price, 2))
