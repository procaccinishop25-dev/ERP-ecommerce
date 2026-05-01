import streamlit as st
import pandas as pd
from supabase import create_client

st.title("🚦 Decision Engine")

# 🔐 credenziali da Streamlit Cloud
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# 📦 dati
data = supabase.table("reorder_decision").select("*").execute().data
df = pd.DataFrame(data)

st.dataframe(df, use_container_width=True)

st.subheader("🔴 Urgenti")

# ⚠️ protezione errori
if not df.empty and "action" in df.columns:
    st.dataframe(df[df["action"] == "🔴 URGENTE"])
else:
    st.warning("Nessuna decisione disponibile")