import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid

st.title("📊 ERP Ecommerce")

# Connessione Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

st.subheader("➕ Inserisci ordine test")

if st.button("Inserisci ordine"):
    try:
        data = {
            "marketplace": "amazon",
            "order_id": str(uuid.uuid4()),  # ID unico
            "order_date": datetime.utcnow().isoformat(),  # timestamp corretto
            "status": "shipped",
            "currency": "EUR",
            "total_amount": 100
        }

        supabase.table("orders").insert(data).execute()
        st.success("✅ Ordine inserito correttamente!")

    except Exception as e:
        st.error(f"❌ Errore: {e}")

# ----------------------------
# 📋 MOSTRA ORDINI
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
