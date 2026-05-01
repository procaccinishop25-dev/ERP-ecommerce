import streamlit as st
import pandas as pd
from supabase import create_client

st.title("🚦 Decision Engine")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

data = supabase.table("decision_engine_final").select("*").execute().data

df = pd.DataFrame(data)

if "id" in df.columns:
    df = df.drop(columns=["id"])

st.subheader("📊 Situazione Stock Intelligente")

st.dataframe(df, use_container_width=True)

st.subheader("🔴 Azioni urgenti")

st.dataframe(df[df["stato"] == "🔴 URGENTE"])
