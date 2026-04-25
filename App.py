import streamlit as st
from supabase import create_client

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

product = {
    "sku": "TSHIRT-001",
    "title": "T-Shirt Black",
    "cost_price": 10,
    "sell_price": 25
}

try:
    res = supabase.table("products").insert(product).execute()
    st.success("Product inserted successfully")
    st.write(res)

except Exception as e:
    st.error("Insert failed")
    st.exception(e)
