import streamlit as st
import pandas as pd
import re
from supabase import create_client
from io import BytesIO

# -------------------------
# SUPABASE
# -------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📦 Multi Marketplace Processor")

# -------------------------
# PRODOTTI SUPABASE
# -------------------------
@st.cache_data
def load_products():
    res = supabase.table("prodotti").select("codice, nome_prodotto").execute()
    return pd.DataFrame(res.data)

products_df = load_products()
product_map = dict(zip(products_df["codice"], products_df["nome_prodotto"]))

# -------------------------
# UPLOAD
# -------------------------
orders_file = st.file_uploader("📄 Amazon ORDINI", type=["csv", "txt"])
comm_file = st.file_uploader("📄 Amazon COMMISSIONI", type=["csv", "txt"])
temu_file = st.file_uploader("📄 TEMU FILE", type=["csv", "txt", "xlsx"])
ebay_orders_file = st.file_uploader("📄 eBay ORDINI", type=["csv", "txt", "xlsx"])
ebay_fee_file = st.file_uploader("📄 eBay COMMISSIONI", type=["csv", "txt", "xlsx"])

# -------------------------
# UTILS
# -------------------------
def extract_code(sku):
    return str(sku).split("_")[1] if "_" in str(sku) else sku

def map_sku(original_sku):
    code = extract_code(original_sku)
    product_name = product_map.get(code)

    if product_name:
        return f"{product_name} - {code}"

    return original_sku

def clean_marketplace(val):
    return str(val).split(".")[0] if pd.notna(val) else val

def find_col(df, keyword):
    for c in df.columns:
        if keyword.lower() in c.lower():
            return c
    return None

def to_float(x):
    try:
        s = str(x)
        s = s.replace("€", "").replace(".", "").replace(",", ".").strip()
        return float(s)
    except:
        return 0.0

def map_country(val):
    if pd.isna(val):
        return ""
    val = str(val).lower()
    return {
        "italy": "IT",
        "germany": "DE",
        "france": "FR",
        "spain": "ES"
    }.get(val, val[:2].upper())

# -------------------------
# AMAZON
# -------------------------
amazon_df = None

if orders_file and comm_file:

    orders = pd.read_csv(orders_file, sep="\t")
    comm = pd.read_csv(comm_file, sep=",")

    comm = comm.rename(columns={
        "Numero di ordine": "amazon-order-id",
        "Commissioni Amazon": "fee"
    })

    df = orders.merge(comm, on="amazon-order-id", how="left")

    df["Data ordine"] = pd.to_datetime(
        df["purchase-date"],
        errors="coerce",
        utc=True
    ).dt.tz_convert("Europe/Rome").dt.tz_localize(None)

    df["Marketplace"] = df["sales-channel"].apply(clean_marketplace)
    df["Prodotto"] = df["sku"].apply(map_sku)

    amazon_df = df[[
        "Data ordine","Marketplace","ship-country","amazon-order-id",
        "Prodotto","quantity","item-price","fee"
    ]].rename(columns={
        "ship-country": "Paese (Mercato)",
        "amazon-order-id": "Order ID (Codice Market)",
        "quantity": "Quantità ordinata",
        "item-price": "Fatturato (Lordo)",
        "fee": "Fee (€)"
    })

# -------------------------
# TEMU
# -------------------------
temu_df = None

if temu_file:

    if temu_file.name.endswith(".xlsx"):
        temu = pd.read_excel(temu_file)
    else:
        temu = pd.read_csv(temu_file, sep="\t", encoding="utf-8", on_bad_lines="skip")

    temu.columns = temu.columns.str.replace("\ufeff", "").str.strip()

    date_col = find_col(temu, "data di acquisto")
    country_col = find_col(temu, "paese")
    order_col = find_col(temu, "id ordine")
    sku_col = find_col(temu, "codice sku")
    qty_col = find_col(temu, "quantità")

    if date_col is None:
        st.error("❌ Colonna data Temu non trovata")
        st.stop()

    t = pd.DataFrame()

    t["Data ordine"] = pd.to_datetime(
        temu[date_col],
        errors="coerce"
    )

    t["Marketplace"] = "Temu"
    t["Paese (Mercato)"] = temu[country_col].apply(map_country)
    t["Order ID (Codice Market)"] = temu[order_col]

    def get_product(row):
        sku = row.get(sku_col)
        name = row.get("nome dell'articolo")

        if pd.notna(sku) and str(sku).strip() != "":
            return map_sku(sku)

        return name

    t["Prodotto"] = temu.apply(get_product, axis=1)

    t["Quantità ordinata"] = pd.to_numeric(
        temu[qty_col],
        errors="coerce"
    ).fillna(0)

    def safe(df, col):
        return df[col].apply(to_float) if col in df.columns else 0

    t["Fatturato (Lordo)"] = (
        safe(temu, "Totale prezzo base dopo lo sconto")
        + safe(temu, "Totale spedizione (imposte escluse)")
        + safe(temu, "Imposta sull'articolo")
        + safe(temu, "Imposta sulla spedizione")
    )

    t["Fee (€)"] = 0.0

    temu_df = t

# -------------------------
# EBAY
# -------------------------
ebay_df = None

if ebay_orders_file and ebay_fee_file:

    ebay_orders = pd.read_excel(ebay_orders_file) if ebay_orders_file.name.endswith(".xlsx") else pd.read_csv(ebay_orders_file, sep="\t")
    ebay_fee = pd.read_excel(ebay_fee_file) if ebay_fee_file.name.endswith(".xlsx") else pd.read_csv(ebay_fee_file, sep=",")

    ebay_orders.columns = ebay_orders.columns.str.strip()
    ebay_fee.columns = ebay_fee.columns.str.strip()

    def clean_fee(x):
        return abs(to_float(x))

    ebay_fee["fee_totale"] = (
        ebay_fee["Commissione sul valore finale - fissa"].apply(clean_fee)
        + ebay_fee["Commissione sul valore finale - variabile"].apply(clean_fee)
        + ebay_fee["Tariffa per l'adeguamento normativo"].apply(clean_fee)
    )

    ebay_fee = ebay_fee.groupby("Numero ordine")["fee_totale"].sum().reset_index()

    df = ebay_orders.merge(ebay_fee, on="Numero ordine", how="left")

    e = pd.DataFrame()

    e["Data ordine"] = pd.to_datetime(
        df["Data vendita"],
        errors="coerce"
    )

    e["Marketplace"] = "eBay"
    e["Paese (Mercato)"] = df["Paese dell'acquirente"].apply(map_country)
    e["Order ID (Codice Market)"] = df["Numero ordine"]

    def get_product_ebay(row):
        sku = row.get("Etichetta personalizzata")
        titolo = row.get("Titolo")

        if pd.notna(sku) and str(sku).strip() != "":
            return map_sku(sku)

        return titolo

    e["Prodotto"] = df.apply(get_product_ebay, axis=1)

    e["Quantità ordinata"] = pd.to_numeric(df["Quantità"], errors="coerce").fillna(0)
    e["Fatturato (Lordo)"] = df["Costo totale"].apply(to_float)
    e["Fee (€)"] = df["fee_totale"].fillna(0)

    ebay_df = e

# -------------------------
# MERGE FINALE
# -------------------------
frames = [f for f in [amazon_df, temu_df, ebay_df] if f is not None]

if frames:

    final_df = pd.concat(frames, ignore_index=True)
    final_df = final_df.sort_values("Data ordine")

    st.success("Elaborazione completata!")
    st.dataframe(final_df)

    output = BytesIO()

    export_df = final_df.copy()

    export_df["Data ordine"] = pd.to_datetime(
        export_df["Data ordine"],
        errors="coerce"
    ).dt.strftime("%d/%m/%Y")

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Orders")

    output.seek(0)

    st.download_button(
        "⬇️ Scarica Excel finale",
        data=output,
        file_name="orders_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
