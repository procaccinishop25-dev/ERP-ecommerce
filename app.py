import streamlit as st
import pandas as pd
from supabase import create_client

# -------------------------
# SUPABASE
# -------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📦 Multi Marketplace Order Processor")

# -------------------------
# PRODOTTI (CACHE)
# -------------------------
@st.cache_data
def load_products():
    res = supabase.table("prodotti").select("codice, nome_prodotto").execute()
    return pd.DataFrame(res.data)

products_df = load_products()
product_map = dict(zip(products_df["codice"], products_df["nome_prodotto"]))


# -------------------------
# FILE UPLOAD
# -------------------------
amazon_orders = st.file_uploader("📄 Amazon ORDINI", type=["csv", "txt"])
amazon_comm = st.file_uploader("📄 Amazon COMMISSIONI", type=["csv", "txt"])
temu_file = st.file_uploader("📄 Temu FILE", type=["csv", "txt"])


# -------------------------
# AMAZON FUNCTIONS
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

    if product_name:
        return f"{product_name} - {code}"

    return original_sku


# -------------------------
# TEMU FUNCTIONS
# -------------------------
def parse_temu_date(date_str):
    dt = pd.to_datetime(date_str, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return None
    return dt.strftime("%d/%m/%Y")


def map_country(val):
    if pd.isna(val):
        return ""
    mapping = {
        "Italy": "IT",
        "Germany": "DE",
        "France": "FR",
        "Spain": "ES"
    }
    return mapping.get(val, str(val)[:2].upper())


def temu_product(row):
    sku = row.get("codice sku")
    name = row.get("nome dell'articolo")

    if pd.notna(sku) and str(sku).strip() != "":
        return sku

    if pd.notna(name):
        return name

    return sku


def temu_gross(row):
    try:
        return (
            float(row.get("totale prezzo base dopo lo sconto", 0) or 0)
            + float(row.get("totale spedizione (imposte escluse)", 0) or 0)
            + float(row.get("imposta sull'articolo", 0) or 0)
            + float(row.get("imposta sulla spedizione", 0) or 0)
        )
    except:
        return 0


# -------------------------
# AMAZON PROCESS
# -------------------------
amazon_df = None

if amazon_orders and amazon_comm:

    orders = pd.read_csv(amazon_orders, sep="\t")
    comm = pd.read_csv(amazon_comm, sep=",")

    comm = comm.rename(columns={
        "Numero di ordine": "amazon-order-id",
        "Commissioni Amazon": "fee"
    })

    df = orders.merge(comm, on="amazon-order-id", how="left")

    df["Data ordine_raw"] = pd.to_datetime(
        df["purchase-date"],
        errors="coerce",
        utc=True
    )

    df["Data ordine"] = df["Data ordine_raw"].dt.strftime("%d/%m/%Y")

    df["Marketplace"] = df["sales-channel"].apply(clean_marketplace)

    df["Prodotto (SKU o nome)"] = df["sku"].apply(map_sku)

    amazon_df = df[[
        "Data ordine",
        "Marketplace",
        "ship-country",
        "amazon-order-id",
        "Prodotto (SKU o nome)",
        "quantity",
        "item-price",
        "fee",
        "Data ordine_raw"
    ]].rename(columns={
        "ship-country": "Paese (Mercato)",
        "amazon-order-id": "Order ID (Codice Market)",
        "quantity": "Quantità ordinata",
        "item-price": "Fatturato (Lordo)",
        "fee": "Fee (€)"
    })


# -------------------------
# TEMU PROCESS (FIX ROBUSTO)
# -------------------------
temu_df = None

if temu_file:

    temu = pd.read_csv(temu_file, sep="\t")

    # FIX CRITICO: pulizia colonne
    temu.columns = (
        temu.columns
        .str.replace("\ufeff", "", regex=True)
        .str.strip()
        .str.lower()
    )

    t = pd.DataFrame()

    # data sicura
    t["Data ordine"] = temu["data di acquisto"].apply(parse_temu_date)

    t["Marketplace"] = "Temu"

    t["Paese (Mercato)"] = temu["paese di spedizione"].apply(map_country)

    t["Order ID (Codice Market)"] = temu["id ordine"]

    t["Prodotto (SKU o nome)"] = temu.apply(temu_product, axis=1)

    t["Quantità ordinata"] = temu["quantità acquistata"]

    t["Fatturato (Lordo)"] = temu.apply(temu_gross, axis=1)

    t["Fee (€)"] = 0.00

    t["Data ordine_raw"] = pd.to_datetime(
        t["Data ordine"],
        dayfirst=True,
        errors="coerce"
    )

    temu_df = t


# -------------------------
# MERGE FINALE
# -------------------------
frames = []

if amazon_df is not None:
    frames.append(amazon_df)

if temu_df is not None:
    frames.append(temu_df)

if frames:

    final_df = pd.concat(frames, ignore_index=True)

    # ordinamento globale
    final_df = final_df.sort_values("Data ordine_raw", ascending=True)

    final_df = final_df.drop(columns=["Data ordine_raw"])

    # -------------------------
    # OUTPUT
    # -------------------------
    st.success("Elaborazione completata!")

    st.dataframe(final_df)

    csv = final_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Scarica file finale",
        csv,
        "orders_final.csv",
        "text/csv"
    )
