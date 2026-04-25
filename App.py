import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.title("📊 ERP Ecommerce - TEST")

# ----------------------------
# 🔌 SUPABASE
# ----------------------------

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# ----------------------------
# ➕ CREA ORDINE COMPLETO
# ----------------------------

st.subheader("➕ Inserisci ordine test (completo)")

if st.button("Inserisci ordine Amazon"):
    try:
        order_id = str(uuid.uuid4())

        # 📦 ORDINE
        supabase.table("orders").insert({
            "marketplace": "amazon",
            "order_id": order_id,
            "order_date": datetime.utcnow().isoformat(),
            "status": "shipped",
            "currency": "EUR",
            "total_amount": 129.99
        }).execute()

        # 📦 ITEMS REALI
        items = [
            {"sku": "NIKE-AIR-M-42", "quantity": 1},
            {"sku": "APPLE-CHARGER-20W", "quantity": 2}
        ]

        # 💰 COSTI (TEST)
        product_costs = {
            "NIKE-AIR-M-42": 55.00,
            "APPLE-CHARGER-20W": 8.50
        }

        # ----------------------------
        # LOOP ITEMS
        # ----------------------------

        for item in items:
            sku = item["sku"]
            qty = item["quantity"]

            # 1. ORDER ITEMS (DB)
            supabase.table("order_items").insert({
                "order_id": order_id,
                "sku": sku,
                "title": sku,
                "quantity": qty,
                "price": 0
            }).execute()

            # 2. MOVIMENTO MAGAZZINO
            supabase.table("inventory_movements").insert({
                "sku": sku,
                "type": "OUT",
                "quantity": qty,
                "reference": order_id,
                "reason": "sale"
            }).execute()

            # 3. INVENTORY UPDATE
            inv = supabase.table("inventory").select("*").eq("sku", sku).execute().data

            if inv:
                new_stock = inv[0]["stock"] - qty

                supabase.table("inventory").update({
                    "stock": new_stock,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("sku", sku).execute()

            else:
                supabase.table("inventory").insert({
                    "sku": sku,
                    "stock": -qty
                }).execute()

        st.success("✅ Ordine completo creato (orders + items + stock)")

    except Exception as e:
        st.error(f"❌ Errore: {e}")

# ----------------------------
# 📦 ORDINI
# ----------------------------

st.subheader("📦 Ordini")

orders = supabase.table("orders").select("*").order("created_at", desc=True).limit(10).execute().data
st.dataframe(orders)

# ----------------------------
# 📜 ORDER ITEMS
# ----------------------------

st.subheader("📦 Order Items")

items = supabase.table("order_items").select("*").order("created_at", desc=True).limit(20).execute().data
st.dataframe(items)

# ----------------------------
# 📦 MOVIMENTI
# ----------------------------

st.subheader("📦 Movimenti magazzino")

movements = supabase.table("inventory_movements").select("*").order("created_at", desc=True).limit(20).execute().data
st.dataframe(movements)

# ----------------------------
# 📦 INVENTORY
# ----------------------------

st.subheader("📦 Stock attuale")

inventory = supabase.table("inventory").select("*").execute().data
st.dataframe(inventory)

# ----------------------------
# 💰 PROFITTO BASE (SEMPLICE E SICURO)
# ----------------------------

st.subheader("💰 Profitto (test)")

product_costs = {
    "NIKE-AIR-M-42": 55.00,
    "APPLE-CHARGER-20W": 8.50
}

orders = supabase.table("orders").select("*").execute().data
items = supabase.table("order_items").select("*").execute().data

result = []

for order in orders:
    order_id = order["order_id"]
    revenue = order["total_amount"]

    order_items = [i for i in items if i["order_id"] == order_id]

    cost = 0

    for i in order_items:
        cost += product_costs.get(i["sku"], 0) * i["quantity"]

    profit = revenue - cost - 12.5  # fee simulata

    result.append({
        "order_id": order_id,
        "revenue": revenue,
        "cost": cost,
        "fees": 12.5,
        "profit": profit
    })

st.dataframe(result)
