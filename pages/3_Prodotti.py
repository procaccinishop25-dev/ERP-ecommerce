import streamlit as st
import pandas as pd
from supabase import create_client

st.title("📦 Prodotti")

# 🔐 credenziali da Streamlit Cloud
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# 📦 dati
products = supabase.table("products").select("*").execute().data
df = pd.DataFrame(products)

st.dataframe(df, use_container_width=True)