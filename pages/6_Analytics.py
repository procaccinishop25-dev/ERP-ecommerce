import streamlit as st
import pandas as pd
from supabase import create_client

st.title("📈 Analytics")

# 🔐 credenziali da Streamlit Cloud
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# 📦 dati
orders = supabase.table("orders").select("*").execute().data
df = pd.DataFrame(orders)

# ⚠️ sicurezza dati vuoti
if df.empty:
    st.warning("Nessun ordine disponibile")
    st.stop()

# 📅 conversione date sicura
if "order_date" in df.columns:
    df["order_date"] = pd.to_datetime(df["order_date"])
else:
    st.warning("Colonna order_date mancante")
    st.stop()

# 💰 verifica colonna importo
if "total_amount" not in df.columns:
    st.warning("Colonna total_amount mancante")
    st.stop()

# 📊 aggregazione
chart_data = df.groupby("order_date")["total_amount"].sum()

st.subheader("📈 Vendite nel tempo")
st.line_chart(chart_data)