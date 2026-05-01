import streamlit as st
from db import supabase

def show():
    st.title("Ordini")

    res = supabase.table("ordini").select("*").execute()

    st.dataframe(res.data)
