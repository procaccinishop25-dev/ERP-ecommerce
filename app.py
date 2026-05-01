import streamlit as st
import pandas as pd

from config.marketplaces import MARKETPLACES
from services.import_engine import import_orders

# ======================
# TITOLO
# ======================
st.title("ERP Ecommerce - Import Temu")

# ======================
# SIDEBAR (INPUT UTENTE)
# ======================
st.sidebar.header("Impostazioni import")

marketplace = st.sidebar.selectbox(
    "Marketplace",
    list(MARKETPLACES.keys())
)

mercato = st.sidebar.selectbox(
    "Mercato",
    ["IT", "EU"]
)

st.sidebar.info("Seleziona marketplace e mercato prima di importare")

config = MARKETPLACES[marketplace]

# ======================
# UPLOAD FILE
# ======================
file = st.file_uploader("Carica Excel", type=["xlsx"])

# ======================
# PREVIEW DATI
# ======================
if file:

    df = pd.read_excel(file)

    # pulizia colonne (FONDAMENTALE)
    df.columns = df.columns.str.strip()

    st.subheader("Anteprima dati")
    st.write("Colonne trovate:")
    st.write(df.columns.tolist())

    st.dataframe(df)

    # ======================
    # IMPORT BUTTON
    # ======================
    if st.button("🚀 Importa dati su ERP"):

        with st.spinner("Import in corso..."):

            import_orders(df, config, marketplace, mercato)

        st.success("Import completato con successo ✅")
