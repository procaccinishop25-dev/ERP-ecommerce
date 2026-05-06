import streamlit as st
import pandas as pd
from supabase import create_client

# -------------------------
# SUPABASE (st.secrets)
# -------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📦 Amazon Order Processor")

# -------------------------
# CACHE PRODOTTI (IMPORTANTISSIMO)
# -------------------------
@st.cache_data
def load_products():
    res = supabase.table("prodotti").select("codice, nome_prodotto").execute()
    df = pd.DataFrame(res.data)
    return df

products_df = load_products()

# trasformo in dict per velocità O(1)
product_map = dict(zip(products_df["codice"], products_df["nome_prodotto"]))


# -------------------------
# UPLOAD FILE
# -------------------------
orders_file = st.file_uploader("📄 File ORDINI Amazon", type=["csv", "txt"])
comm_file = st.file_uploader("📄 File COMMISSIONI", type=["csv", "txt"])


# -------------------------
# FUNZIONI
# -------------------------
def format_date(date_str):
    return pd.to_datetime(date_str).strftime("%d/%m/%Y")


def clean_marketplace(val):
    if pd.isna(val):
        return val
    return str(val).split(".")[0]


def extract_sku(sku):
    if "_" in str(sku):
        return str(sku).split("_")[1]
    return sku


def map_product(sku):
    return product_map.get(sku, sku)  # fallback = SKU originale


# -------------------------
# PROCESSING
# -------------------------
if orders_file and comm_file:

    # ORDINI AMAZON (TSV)
    orders = pd.read_csv(orders_file, sep="\t")

    # COMMISSIONI
    comm = pd.read_csv(comm_file, sep=",")

    comm = comm.rename(columns={
        "Numero di ordine": "amazon-order-id",
        "Commissioni Amazon": "fee"
    })

    # MERGE
    df = orders.merge(comm, on="amazon-order-id", how="left")

    # -------------------------
    # TRASFORMAZIONI
    # -------------------------

    # DATA
    df["Data ordine"] = df["purchase-date"].apply(format_date)

    # MARKETPLACE
    df["Marketplace"] = df["sales-channel"].apply(clean_marketplace)

    # SKU CLEAN
    df["sku_clean"] = df["sku"].apply(extract_sku)

    # PRODOTTO DA SUPABASE
    df["Prodotto"] = df["sku_clean"].apply(map_product)

    # -------------------------
    # OUTPUT FINALE
    # -------------------------
    output = df[[
        "Data ordine",
        "Marketplace",
        "ship-country",
        "amazon-order-id",
        "Prodotto",
        "quantity",
        "item-price",
        "fee"
    ]]

    st.success("Elaborazione completata!")

    st.dataframe(output)

    # -------------------------
    # DOWNLOAD
    # -------------------------
    csv = output.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Scarica Excel finale",
        csv,
        "amazon_output.csv",
        "text/csv"
    )
