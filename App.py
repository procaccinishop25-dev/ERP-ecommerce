import streamlit as st
from supabase import create_client

st.title("ERP Ecommerce")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

if st.button("Inserisci ordine test"):
    data = {
        "marketplace": "amazon",
        "order_id": "STREAMLIT_TEST",
        "status": "shipped",
        "currency": "EUR",
        "total_amount": 100
    }

    supabase.table("orders").insert(data).execute()
    st.success("Ordine inserito!")
