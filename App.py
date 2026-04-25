import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.title("📊 ERP Ecommerce")

# ----------------------------
# 🔌 CONNESSIONE SUPABASE
# ----------------------------

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

# ----------------------------
# ➕ INSERIMENTO ORDINE
# ----------------------------

st.subheader("➕ Inserisci ordine test")

if st.button("Inserisci ordine"):
    try:
        order_id = str(uuid.uuid4())

        data = {
            "marketplace": "amazon",
            "order_id": order_id,
            "order_date": datetime.utcnow().isoformat(),
            "status": "shipped",
            "currency": "EUR",
            "total_amount": 100
        }

        # 1. ORDINE
        supabase.table("orders").insert(data).execute()

        # 2. ITEMS TEST
        items = [
            {"sku": "SKU1", "quantity": 1}
        ]

        # 3. MOVIMENTI + INVENTORY
        for item in items:
            sku = item["sku"]
            qty = item["quantity"]

            # MOVIMENTO MAGAZZINO (STORICO)
            supabase.table("inventory_movements").insert({
                "sku": sku,
                "type": "OUT",
                "quantity": qty,
                "reference": order_id,
                "reason": "sale"
            }).execute()

            # INVENTORY (STOCK REALE)
            inv = supabase.table("inventory").select("*").eq("sku", sku).execute().data

            if inv:
                current_stock = inv[0]["stock"]
                new_stock = current_stock - qty

                supabase.table("inventory").update({
                    "stock": new_stock,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("sku", sku).execute()

            else:
                supabase.table("inventory").insert({
                    "sku": sku,
                    "stock": -qty
                }).execute()

        st.success("✅ Ordine + magazzino aggiornati!")

    except Exception as e:
        st.error(f"❌ Errore: {e}")

# ----------------------------
# 📦 ORDINI
# ----------------------------

st.subheader("📦 Ordini salvati")

try:
    orders = supabase.table("orders").select("*").order("created_at", desc=True).limit(10).execute().data
    st.dataframe(orders)
except Exception as e:
    st.error(f"Errore ordini: {e}")

# ----------------------------
# 📜 MOVIMENTI MAGAZZINO
# ----------------------------

st.subheader("📦 Movimenti magazzino")

try:
    movements = supabase.table("inventory_movements").select("*").order("created_at", desc=True).limit(10).execute().data
    st.dataframe(movements)
except Exception as e:
    st.error(f"Errore movimenti: {e}")

# ----------------------------
# 📦 INVENTORY
# ----------------------------

st.subheader("📦 Inventory (stock reale)")

try:
    inventory = supabase.table("inventory").select("*").execute().data
    st.dataframe(inventory)
except Exception as e:
    st.error(f"Errore inventory: {e}")

# ----------------------------
# 📊 PROFITTO ORDINI
# ----------------------------

st.subheader("💰 Profitto ordini (reale)")

try:
    orders = supabase.table("orders").select("*").execute().data
    items = supabase.table("order_items").select("*").execute().data
    products = supabase.table("products").select("*").execute().data
    fees = supabase.table("fees").select("*").execute().data

    product_cost_map = {p["sku"]: p["cost"] for p in products}

    result = []

    for order in orders:
        order_id = order["order_id"]
        revenue = order["total_amount"]

        order_items = [i for i in items if i["order_id"] == order_id]

        product_cost = 0

        for item in order_items:
            sku = item["sku"]
            qty = item["quantity"]
            cost = product_cost_map.get(sku, 0)

            product_cost += cost * qty

        order_fees = sum(f["amount"] for f in fees if f["order_id"] == order_id)

        profit = revenue - product_cost - order_fees

        result.append({
            "order_id": order_id,
            "revenue": revenue,
            "cost": product_cost,
            "fees": order_fees,
            "profit": profit
        })

    st.dataframe(result)

except Exception as e:
    st.error(f"Errore profitto: {e}")
