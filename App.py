import streamlit as st
from supabase import create_client

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(URL, KEY)

st.title("Insert Product")

product = {
    "sku": "TSHIRT-001",
    "title": "T-Shirt Black",
    "cost_price": 10,
    "sell_price": 25
}

if st.button("Insert product"):
    res = supabase.table("products").insert(product).execute()
    st.success("Product inserted")
    st.write(res)
