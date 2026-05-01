import streamlit as st
import pandas as pd
from supabase import create_client

st.title("📦 Ordini")

# 🔐 credenziali da Streamlit Cloud secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# 📦 dati
orders = supabase.table("orders").select("*").execute().data
df = pd.DataFrame(orders)

st.dataframe(df, use_container_width=True)