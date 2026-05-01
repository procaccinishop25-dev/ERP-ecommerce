import streamlit as st
import pandas as pd

from config.marketplaces import MARKETPLACES
from services.import_engine import import_orders


# ======================
# UI
# ======================
st.title("ERP Ecommerce")

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


# ======================
# FILE UPLOAD
# ======================
file = st.file_uploader("Carica Excel", type=["xlsx"])


if file:

    df = pd.read_excel(file)

    df.columns = df.columns.str.strip()

    st.subheader("Preview dati")
    st.write(df.columns.tolist())
    st.dataframe(df)

    if st.button("Importa dati"):

        with st.spinner("Import in corso..."):

            import_orders(df, config, marketplace, mercato)

        st.success("Import completato ✅")
