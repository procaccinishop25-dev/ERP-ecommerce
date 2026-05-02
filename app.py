import streamlit as st
from core.router import parse_file
from core.importer import save_orders

st.title("📦 ERP System")

marketplace = st.selectbox("Marketplace", ["temu", "amazon"])

file = st.file_uploader("Carica file")

if file:

    orders = parse_file(file, marketplace)

    st.write(f"Ordini trovati: {len(orders)}")

    if st.button("🚀 Importa"):

        save_orders(orders)
        st.success("Import completato")
