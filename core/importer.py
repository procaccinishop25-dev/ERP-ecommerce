from supabase import create_client
import streamlit as st

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

def save_orders(orders):

    for order in orders.values():

        res = supabase.table("orders").insert({
            "order_id": order["order_id"],
            "marketplace": "temu",
            "country": order["country"],
            "order_date": str(order["date"]) if order["date"] is not None else None
        }).execute()

        order_db_id = res.data[0]["id"]

        for item in order["items"]:

            supabase.table("order_items").insert({
                "order_id": order_db_id,
                "sku": item["sku"],
                "quantity": item["qty"],
                "revenue": item["revenue"]
            }).execute()
