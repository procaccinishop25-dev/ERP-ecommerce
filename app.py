import streamlit as st
import pandas as pd

from config.marketplaces import MARKETPLACES
from services.import_engine import import_orders

st.title("ERP Ecommerce - Temu Base")

# =====================
# SIDEBAR
# =====================
st.sidebar.header("Impostazioni")

marketplace = st.sidebar.selectbox(
    "Marketplace",
    list(MARKETPLACES.keys())
)

mercato = st.sidebar.selectbox(
    "Mercato",
    ["IT", "EU"]
)

config = MARKETPLACES[marketplace]

# =====================
# UPLOAD FILE
# =====================
file = st.file_uploader("Carica Excel Temu", type=["xlsx"])

if file:

    df = pd.read_excel(file)

    # debug (IMPORTANTE)
    st.write("Colonne trovate:")
    st.write(df.columns.tolist())

    st.dataframe(df)

    # =====================
    # IMPORT
    # =====================
    if st.button("Importa dati"):

        import_orders(df, config, marketplace, mercato)

        st.success("Import completato ✅")
