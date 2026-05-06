import streamlit as st
import pandas as pd
from supabase import create_client

# -------------------------
# SUPABASE (SECRETS)
# -------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📦 Amazon Order Processor")

# -------------------------
# CARICA PRODOTTI (CACHE)
# -------------------------
@st.cache_data
def load_products():
    res = supabase.table("prodotti").select("codice, nome_prodotto").execute()
    return pd.DataFrame(res.data)

products_df = load_products()

# dizionario veloce: codice → nome prodotto
product_map = dict(zip(products_df["codice"], products_df["nome_prodotto"]))


# -------------------------
# UPLOAD FILE
# -------------------------
orders_file = st.file_uploader("📄 File ORDINI Amazon", type=["csv", "txt"])
comm_file = st.file_uploader("📄 File COMMISSIONI Amazon", type=["csv", "txt"])


# -------------------------
# FUNZIONI
# -------------------------
def clean_marketplace(val):
    if pd.isna(val):
        return val
    return str(val).split(".")[0]


def extract_code(sku):
    if "_" in str(sku):
        return str(sku).split("_")[1]
    return sku


def map_sku(original_sku):
    code = extract_code(original_sku)

    product_name = product_map.get(code)

    # CASO TROVATO
    if product_name:
        return f"{product_name} - {code}"

    # CASO NON TROVATO → ritorna input originale
    return original_sku


# -------------------------
# PROCESSING
# -------------------------
if orders_file and comm_file:

    # ORDINI (TSV Amazon)
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

    # DATA (raw per sorting)
    df["Data ordine_raw"] = pd.to_datetime(df["purchase-date"])

    df["Data ordine"] = df["Data ordine_raw"].dt.strftime("%d/%m/%Y")

    # MARKETPLACE
    df["Marketplace"] = df["sales-channel"].apply(clean_marketplace)

    # SKU → PRODOTTO
    df["Prodotto"] = df["sku"].apply(map_sku)

    # -------------------------
    # ORDINAMENTO
    # -------------------------
    df = df.sort_values("Data ordine_raw", ascending=True)

    # rimuovo colonna tecnica
    df = df.drop(columns=["Data ordine_raw"])

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
        "⬇️ Scarica file finale",
        csv,
        "amazon_output.csv",
        "text/csv"
    )
