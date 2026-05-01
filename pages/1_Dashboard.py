import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("📊 Dashboard")

orders = supabase.table("orders").select("*").execute().data
decisions = supabase.table("reorder_decision").select("*").execute().data

df_orders = pd.DataFrame(orders)
df_decisions = pd.DataFrame(decisions)

# KPI
col1, col2, col3 = st.columns(3)

col1.metric("Ordini", len(df_orders))
col2.metric("Fatturato", f"€ {df_orders['total_amount'].sum() if 'total_amount' in df_orders else 0}")
col3.metric("Prodotti a rischio", len(df_decisions[df_decisions["action"] == "🔴 URGENTE"]))

st.divider()

st.subheader("🚦 Decision Engine")
st.dataframe(df_decisions, use_container_width=True)