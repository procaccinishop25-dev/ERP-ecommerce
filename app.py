import streamlit as st
from core.temu_parser import parse_temu
from core.importer import save_orders

st.title("📦 ERP Temu Import")

file = st.file_uploader("Carica Excel Temu")

if file:

    orders = parse_temu(file)

    st.success(f"Ordini trovati: {len(orders)}")

    if st.button("🚀 Importa su Supabase"):

        save_orders(orders)
        st.success("Import completato")
