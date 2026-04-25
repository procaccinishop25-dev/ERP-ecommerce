import streamlit as st
from supabase import create_client
import pandas as pd

# ======================
# SUPABASE
# ======================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.set_page_config(page_title="ERP Dashboard", layout="wide")

st.title("📊 Ecommerce ERP Dashboard")

# ======================
# LOAD DATA
# ======================
orders_res = supabase.table("orders").select("*").execute()
products_res = supabase.table("products").select("*").execute()

orders = pd.DataFrame(orders_res.data)
products = pd.DataFrame(products_res.data)

# ======================
# KPI SECTION
# ======================
col1, col2, col3 = st.columns(3)

if not orders.empty:
    total_revenue = orders["total_amount"].sum()
    total_profit = orders["net_profit"].sum()
    total_orders = len(orders)
else:
    total_revenue = total_profit = total_orders = 0

col1.metric("💰 Revenue", f"€ {total_revenue}")
col2.metric("📈 Profit", f"€ {total_profit}")
col3.metric("📦 Orders", total_orders)

st.divider()

# ======================
# ORDERS TABLE
# ======================
st.subheader("📦 Orders")

if not orders.empty:
    st.dataframe(orders, use_container_width=True)
else:
    st.info("No orders yet")

# ======================
# PRODUCTS TABLE
# ======================
st.subheader("🛍️ Products")

if not products.empty:
    st.dataframe(products, use_container_width=True)
else:
    st.info("No products yet")
