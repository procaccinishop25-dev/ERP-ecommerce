import streamlit as st
import pandas as pd

from config.marketplaces import MARKETPLACES
from services.import_engine import import_orders

st.title("ERP Ecommerce")

# --------------------
# SELECT MARKETPLACE
# --------------------
marketplace = st.selectbox("Marketplace", list(MARKETPLACES.keys()))
mercato = st.selectbox("Mercato", ["IT", "EU"])

config = MARKETPLACES[marketplace]

# --------------------
# UPLOAD FILE
# --------------------
file = st.file_uploader("Carica Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    st.dataframe(df)

    if st.button("Importa dati"):

        import_orders(df, config, marketplace, mercato)

        st.success("Import completato")
