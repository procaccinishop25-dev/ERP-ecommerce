import streamlit as st
from supabase import create_client
import pandas as pd

# ======================
# CONFIG
# ======================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.set_page_config(
    page_title="ERP Dashboard",
    page_icon="📊",
    layout="wide"
)

# ======================
# SIDEBAR FILTERS
# ======================
st.sidebar.title("⚙️ Filters")

country_filter = st.sidebar.selectbox(
    "Country",
    ["ALL", "IT", "DE"]
)

marketplace_filter = st.sidebar.selectbox(
    "Marketplace",
    ["ALL", "amazon", "ebay"]
)

st.title("📊 Ecommerce ERP Dashboard")

# ======================
# LOAD DATA
# ======================
orders_res = supabase.table("orders").select("*").execute()
products_res = supabase.table("products").select("*").execute()

orders = pd.DataFrame(orders_res.data)
products = pd.DataFrame(products_res.data)

# ======================
# FILTER DATA
# ======================
if not orders.empty:

    if country_filter != "ALL":
        orders = orders[orders["country"] == country_filter]

    if marketplace_filter != "ALL":
        orders = orders[orders["marketplace"] == marketplace_filter]

# ======================
# KPI CARDS
# ======================
col1, col2, col3, col4 = st.columns(4)

if not orders.empty:
    revenue = orders["total_amount"].sum()
    profit = orders["net_profit"].sum()
    avg_order = orders["total_amount"].mean()
    orders_count = len(orders)
else:
    revenue = profit = avg_order = orders_count = 0

col1.metric("💰 Revenue", f"€ {revenue:.2f}")
col2.metric("📈 Profit", f"€ {profit:.2f}")
col3.metric("🧾 Orders", orders_count)
col4.metric("📊 Avg Order", f"€ {avg_order:.2f}")

st.divider()

# ======================
# ORDERS TABLE
# ======================
st.subheader("📦 Orders")

if not orders.empty:
    st.dataframe(
        orders.sort_values("order_date", ascending=False),
        use_container_width=True
    )
else:
    st.info("No orders found")

# ======================
# PRODUCTS TABLE
# ======================
st.subheader("🛍️ Products")

if not products.empty:
    st.dataframe(
        products,
        use_container_width=True
    )
else:
    st.info("No products found")
