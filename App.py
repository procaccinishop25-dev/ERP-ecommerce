import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.title("📊 ERP Ecommerce")

# Connessione Supabase
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

        # 1. inserisci ordine
        supabase.table("orders").insert(data).execute()

        # 2. SIMULAZIONE order_items (per test)
        items = [
            {"sku": "SKU1", "quantity": 1}
        ]

        # 3. CREA MOVIMENTI MAGAZZINO
        for item in items:
            supabase.table("inventory_movements").insert({
                "sku": item["sku"],
                "type": "OUT",
                "quantity": item["quantity"],
                "reference": order_id,
                "reason": "sale"
            }).execute()

        st.success("✅ Ordine + movimenti magazzino creati!")

    except Exception as e:
        st.error(f"❌ Errore: {e}")

# ----------------------------
# 📋 ORDINI
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
    st.error(f"Errore caricamento ordini: {e}")

# ----------------------------
# 📦 MOVIMENTI MAGAZZINO
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
    st.error(f"Errore caricamento magazzino: {e}")
