import streamlit as st
from supabase import create_client

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# 👉 INPUT ORDINE (come da Amazon/eBay)
sku = "TSHIRT-001"
sell_price = 25
fees = 5

# 1. prendi prodotto dal DB
product_res = supabase.table("products").select("*").eq("sku", sku).single().execute()

product = product_res.data
cost_price = product["cost_price"]

# 2. calcolo profitto
profit = sell_price - cost_price - fees

# 3. salva ordine
order = {
    "marketplace": "amazon",
    "country": "IT",
    "order_date": "now",
    "total_amount": sell_price,
    "fees": fees,
    "shipping_cost": 0,
    "net_profit": profit
}

res = supabase.table("orders").insert(order).execute()

st.success("Order created automatically")
st.write("Profit:", profit)
st.write(res)
