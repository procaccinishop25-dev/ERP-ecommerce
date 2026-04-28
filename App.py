import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# 🔐 CONFIG SUPABASE
# =========================
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "LA_TUA_ANON_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 🧠 DASHBOARD
# =========================
st.set_page_config(page_title="ERP Ecommerce Dashboard", layout="wide")
st.title("📊 ERP Ecommerce Dashboard")


# =========================
# 📦 UTILITY FUNCTION
# =========================
def fetch_table(table_name: str):
    """Recupera dati da Supabase e li converte in DataFrame."""
    response = supabase.table(table_name).select("*").execute()
    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame()


def show_dataframe(df: pd.DataFrame, empty_msg: str):
    """Mostra dataframe o warning se vuoto."""
    if df.empty:
        st.warning(empty_msg)
        return False
    st.dataframe(df, use_container_width=True)
    return True


# =========================
# 📦 ORDERS
# =========================
st.subheader("📦 Ordini")

df_orders = fetch_table("orders")

if not df_orders.empty:
    col1, col2 = st.columns(2)
    col1.metric("Totale ordini", len(df_orders))
    col2.metric("Fatturato totale", f"€ {df_orders['revenue'].sum():,.2f}")

    show_dataframe(df_orders, "Nessun ordine trovato")
else:
    st.warning("Nessun ordine trovato")


# =========================
# 📦 PRODUCTS
# =========================
st.subheader("📦 Prodotti")

df_products = fetch_table("products")

if not df_products.empty:
    st.metric("Totale prodotti", len(df_products))
    show_dataframe(df_products, "Nessun prodotto trovato")
else:
    st.warning("Nessun prodotto trovato")


# =========================
# 🧱 STOCK MOVEMENTS
# =========================
st.subheader("📦 Movimenti Magazzino")

df_stock = fetch_table("stock_movements")

show_dataframe(df_stock, "Nessun movimento stock trovato")
