import streamlit as st
import pandas as pd
from supabase import create_client

from adapters.temu import transform as temu_transform
from adapters.ebay import transform as ebay_transform
from core.importer import import_to_supabase

# secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

st.title("Import Ordini Universale")

marketplace = st.selectbox("Marketplace", ["TEMU", "EBAY"])
mercato = st.text_input("Mercato")

file = st.file_uploader("Carica Excel")

if file:

    df = pd.read_excel(file)
    st.dataframe(df.head())

    if st.button("IMPORTA"):

        if marketplace == "TEMU":
            data = temu_transform(df, marketplace, mercato)

        elif marketplace == "EBAY":
            data = ebay_transform(df, marketplace, mercato)

        order_id = import_to_supabase(data, supabase)

        st.success(f"Import completato: {order_id}")
