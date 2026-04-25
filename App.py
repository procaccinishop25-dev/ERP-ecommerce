import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.title("📊 ERP Ecommerce (Realistico)")

# ----------------------------
# 🔌 SUPABASE
# ----------------------------

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# ============================
# ➕ ORDINE REALISTICO
# ============================

st.subheader("➕ Inserisci ordine test (realistico)")

if st.button("Inserisci ordine Amazon"):
    try:
        order_id = str(uuid.uuid4())

        # 🧾 ORDINE REALE SIMULATO
        order_data = {
            "marketplace": "amazon",
            "order_id": order_id,
            "order_date": datetime.utcnow().isoformat(),
            "status": "shipped",
            "currency": "EUR",
            "total_amount": 129.99
        }

        supabase.table("orders").insert(order_data).execute()

        # 📦 ORDER ITEMS REALI
        items = [
            {"sku": "NIKE-AIR-M-42", "quantity": 1},
            {"sku": "APPLE-CHARGER-20W", "quantity": 2}
        ]

        # 💰 COSTI PRODOTTI REALI (semplificati)
        product_costs = {
            "NIKE-AIR-M-42": 55.00,
            "APPLE-CHARGER-20W": 8.50
        }

        # 📊 FEES AMAZON SIMULATE
        fees_total = 12.50

        # ============================
        # 📦 MAGAZZINO + MOVIMENTI
        # ============================

        for item in items:
            sku = item["sku"]
            qty = item["quantity"]

            # MOVIMENTO STOCK
            supabase.table("inventory_movements").insert({
                "sku": sku,
                "type": "OUT",
                "quantity": qty,
                "reference": order_id,
                "reason": "sale"
            }).execute()

            # INVENTORY UPDATE
            inv = supabase.table("inventory").select("*").eq("sku", sku).execute().data

            cost = product_costs.get(sku, 0)

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

        st.success("✅ Ordine Amazon creato (realistico)")

    except Exception as e:
        st.error(f"Errore: {e}")

# ============================
# 📦 ORDINI
# ============================

st.subheader("📦 Ordini")

orders = supabase.table("orders").select("*").order("created_at", desc=True).limit(10).execute().data
st.dataframe(orders)

# ============================
# 📜 MOVIMENTI
# ============================

st.subheader("📦 Movimenti magazzino")

movements = supabase.table("inventory_movements").select("*").order("created_at", desc=True).limit(10).execute().data
st.dataframe(movements)

# ============================
# 📦 INVENTORY
# ============================

st.subheader("📦 Stock attuale")

inventory = supabase.table("inventory").select("*").execute().data
st.dataframe(inventory)

# ============================
# 💰 PROFITTO REALE
# ============================

st.subheader("💰 Profitto ordini (reale)")

orders = supabase.table("orders").select("*").execute().data
items = supabase.table("order_items").select("*").execute().data
fees = supabase.table("fees").select("*").execute().data

# costi realistici
product_costs = {
    "NIKE-AIR-M-42": 55.00,
    "APPLE-CHARGER-20W": 8.50
}

result = []

for order in orders:
    order_id = order["order_id"]

    revenue = order["total_amount"]

    order_items = [i for i in items if i["order_id"] == order_id]

    cost = 0

    for item in order_items:
        sku = item["sku"]
        qty = item["quantity"]
        cost += product_costs.get(sku, 0) * qty

    fee_cost = 12.50  # simulazione Amazon fee

    profit = revenue - cost - fee_cost

    result.append({
        "order_id": order_id,
        "revenue": revenue,
        "cost": cost,
        "fees": fee_cost,
        "profit": profit
    })

st.dataframe(result)
