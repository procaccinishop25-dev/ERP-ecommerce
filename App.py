from supabase import create_client
import streamlit as st

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(URL, KEY)

data = {
    "marketplace": "amazon",
    "country": "IT",
    "order_date": "2026-04-25T10:00:00",
    "total_amount": 100,
    "fees": 10,
    "shipping_cost": 0,
    "net_profit": 90
}

res = supabase.table("orders").insert(data).execute()

print(res)
