import streamlit as st
import pandas as pd
from supabase import create_client

from adapters.temu import transform as temu_transform
from core.importer import import_to_supabase

# 🔐 secrets Streamlit Cloud
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

st.title("Import Ordini Universale")

marketplace = st.selectbox("Marketplace", ["TEMU"])
mercato = st.text_input("Mercato", "IT")

file = st.file_uploader("Carica Excel")

if file:

    df = pd.read_excel(file)

    st.write("📌 Colonne rilevate:")
    st.write(list(df.columns))

    st.write("Preview:")
    st.dataframe(df.head())

    if st.button("IMPORTA"):

        data = temu_transform(df, marketplace, mercato)

        order_id = import_to_supabase(data, supabase)

        st.success(f"Import completato: {order_id}")
