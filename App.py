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

        # 1. INSERISCI ORDINE
        supabase.table("orders").insert(data).execute()

        # 2. SIMULAZIONE ORDER ITEMS
        items = [
            {"sku": "SKU1", "quantity": 1}
        ]

        # 3. MOVIMENTI + INVENTORY UPDATE
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
    response = supabase.table("orders").select("*").order("created_at", desc=True).limit(10).execute()
    orders = response.data

    if orders:
        st.dataframe(orders)
    else:
        st.info("Nessun ordine presente")

except Exception as e:
    st.error(f"Errore ordini: {e}")

# ----------------------------
# 📜 MOVIMENTI MAGAZZINO
# ----------------------------

st.subheader("📦 Movimenti magazzino")

try:
    response = supabase.table("inventory_movements").select("*").order("created_at", desc=True).limit(10).execute()
    movements = response.data

    if movements:
        st.dataframe(movements)
    else:
        st.info("Nessun movimento presente")

except Exception as e:
    st.error(f"Errore movimenti: {e}")

# ----------------------------
# 📊 INVENTORY (STOCK REALE DB)
# ----------------------------

st.subheader("📦 Inventory (stock reale)")

try:
    response = supabase.table("inventory").select("*").execute()
    inventory = response.data

    if inventory:
        st.dataframe(inventory)
    else:
        st.info("Nessun inventory presente")

except Exception as e:
    st.error(f"Errore inventory: {e}")

# ----------------------------
# 📊 STOCK CALCOLATO (BACKUP LOGICO)
# ----------------------------

st.subheader("📊 Stock calcolato (da movimenti)")

try:
    response = supabase.table("inventory_movements").select("*").execute()
    movements = response.data

    stock = {}

    for m in movements:
        sku = m["sku"]
        qty = m["quantity"]

        if sku not in stock:
            stock[sku] = 0

        if m["type"] == "IN":
            stock[sku] += qty
        elif m["type"] == "OUT":
            stock[sku] -= qty

    if stock:
        st.dataframe([
            {"sku": k, "stock": v} for k, v in stock.items()
        ])
    else:
        st.info("Nessun dato stock")

except Exception as e:
    st.error(f"Errore stock: {e}")
