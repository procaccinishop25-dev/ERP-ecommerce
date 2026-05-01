import streamlit as st
import pandas as pd
from supabase import create_client

st.title("📦 Magazzino")

# 🔐 credenziali da Streamlit Cloud
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# 📦 dati
stock = supabase.table("stock_coverage").select("*").execute().data
df = pd.DataFrame(stock)

st.subheader("🚦 Stato Stock")
st.dataframe(df, use_container_width=True)

st.subheader("🔴 Critici")

# ⚠️ protezione errore se vuoto
if not df.empty and "days_cover" in df.columns:
    st.dataframe(df[df["days_cover"] < 7])
else:
    st.warning("Nessun dato stock disponibile")