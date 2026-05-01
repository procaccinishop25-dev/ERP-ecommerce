import streamlit as st

def show():
    st.title("Import Ordini")

    marketplace = st.selectbox("Marketplace", ["TEMU"])
    mercato = st.selectbox("Mercato", ["IT", "FR", "DE"])

    file = st.file_uploader("Carica file ordini", type=["xlsx", "csv"])

    if file:
        st.success("File caricato")
