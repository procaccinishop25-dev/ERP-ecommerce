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
# PRODOTTI
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
ebay_orders_file = st.file_uploader("📄 EBAY ORDINI", type=["csv", "txt", "xlsx"])
ebay_fee_file = st.file_uploader("📄 EBAY COMMISSIONI", type=["csv", "txt", "xlsx"])

# -------------------------
# UTILS
# -------------------------
def extract_code(sku):
    return str(sku).split("_")[1] if "_" in str(sku) else sku

def map_sku(original_sku):
    code = extract_code(original_sku)
    return f"{product_map.get(code)} - {code}" if product_map.get(code) else original_sku

def clean_marketplace(val):
    return str(val).split(".")[0] if pd.notna(val) else val

def find_col(df, keyword):
    for c in df.columns:
        if keyword.lower() in c.lower():
            return c
    return None

def to_float(x):
    try:
        return float(str(x).replace("€", "").replace(",", ".").strip())
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
# TEMU DATE
# -------------------------
def parse_temu_date(x):
    if pd.isna(x):
        return pd.NaT

    x = str(x)
    x = re.sub(r"CEST.*", "", x).strip()

    mesi = {
        "gen":"Jan","feb":"Feb","mar":"Mar","apr":"Apr",
        "mag":"May","giu":"Jun","lug":"Jul","ago":"Aug",
        "set":"Sep","ott":"Oct","nov":"Nov","dic":"Dec"
    }

    for it, en in mesi.items():
        x = x.replace(it, en)

    return pd.to_datetime(x, errors="coerce")

# -------------------------
# EBAY DATE (FIX DEFINITIVO)
# -------------------------
def parse_ebay_date(x):
    if pd.isna(x):
        return pd.NaT

    x = str(x).lower()

    mesi = {
        "gen":"Jan","feb":"Feb","mar":"Mar","apr":"Apr",
        "mag":"May","giu":"Jun","lug":"Jul","ago":"Aug",
        "set":"Sep","ott":"Oct","nov":"Nov","dic":"Dec"
    }

    for it, en in mesi.items():
        x = x.replace(f" {it} ", f" {en} ")

    return pd.to_datetime(x, errors="coerce")

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

    df["Data ordine"] = pd.to_datetime(df["purchase-date"], errors="coerce", utc=True)\
        .dt.strftime("%d/%m/%Y")

    df["Marketplace"] = df["sales-channel"].apply(clean_marketplace)
    df["Prodotto"] = df["sku"].apply(map_sku)

    amazon_df = df[[
        "Data ordine","Marketplace","ship-country","amazon-order-id",
        "Prodotto","quantity","item-price","fee"
    ]].rename(columns={
        "ship-country":"Paese (Mercato)",
        "amazon-order-id":"Order ID (Codice Market)",
        "quantity":"Quantità ordinata",
        "item-price":"Fatturato (Lordo)",
        "fee":"Fee (€)"
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

    temu.columns = temu.columns.str.strip()

    date_col = find_col(temu, "acquisto")
    country_col = find_col(temu, "paese")
    order_col = find_col(temu, "id ordine")
    sku_col = find_col(temu, "codice sku")
    qty_col = find_col(temu, "quantità")

    t = pd.DataFrame()

    t["Data ordine"] = temu[date_col].apply(parse_temu_date).dt.strftime("%d/%m/%Y")
    t["Marketplace"] = "Temu"
    t["Paese (Mercato)"] = temu[country_col].apply(map_country)
    t["Order ID (Codice Market)"] = temu[order_col]

    def get_product(row):
        sku = row.get(sku_col)
        name = row.get("nome dell'articolo")
        return sku if pd.notna(sku) and str(sku).strip() != "" else name

    t["Prodotto"] = temu.apply(get_product, axis=1)
    t["Quantità ordinata"] = pd.to_numeric(temu[qty_col], errors="coerce").fillna(0)

    def safe(col):
        return temu[col].apply(to_float) if col in temu.columns else 0

    t["Fatturato (Lordo)"] = (
        safe("Totale prezzo base dopo lo sconto")
        + safe("Totale spedizione (imposte escluse)")
        + safe("Imposta sull'articolo")
        + safe("Imposta sulla spedizione")
    )

    t["Fee (€)"] = 0.0

    temu_df = t

# -------------------------
# EBAY (FIX DEFINITIVO)
# -------------------------
ebay_df = None

if ebay_orders_file and ebay_fee_file:

    ebay_orders = pd.read_excel(ebay_orders_file)
    ebay_fee = pd.read_excel(ebay_fee_file)

    ebay_orders.columns = ebay_orders.columns.str.strip()
    ebay_fee.columns = ebay_fee.columns.str.strip()

    # somma tutte le fee (incluse ads)
    def calc_fee(row):
        total = 0.0
        for v in row:
            try:
                v = str(v)
                if "-" in v:
                    total += abs(to_float(v))
            except:
                pass
        return total

    ebay_fee["fee_totale"] = ebay_fee.apply(calc_fee, axis=1)
    ebay_fee = ebay_fee.groupby("Numero ordine", as_index=False)["fee_totale"].sum()

    df = ebay_orders.merge(ebay_fee, on="Numero ordine", how="left")

    e = pd.DataFrame()

    # 🔥 FIX CRITICO: apply corretto (NON più errore ValueError)
    e["Data ordine"] = df["Data vendita"].apply(parse_ebay_date).dt.strftime("%d/%m/%Y")

    e["Marketplace"] = "eBay"
    e["Paese (Mercato)"] = df["Paese dell'acquirente"].apply(map_country)
    e["Order ID (Codice Market)"] = df["Numero ordine"]

    def get_product_ebay(row):
        sku = row.get("Etichetta personalizzata")
        titolo = row.get("Titolo")
        return map_sku(sku) if pd.notna(sku) and str(sku).strip() != "" else titolo

    e["Prodotto"] = df.apply(get_product_ebay, axis=1)
    e["Quantità ordinata"] = pd.to_numeric(df["Quantità"], errors="coerce").fillna(0)
    e["Fatturato (Lordo)"] = df["Costo totale"].apply(to_float)
    e["Fee (€)"] = df["fee_totale"].fillna(0)

    ebay_df = e

# -------------------------
# MERGE FINALE
# -------------------------
frames = []

if amazon_df is not None:
    frames.append(amazon_df)

if temu_df is not None:
    frames.append(temu_df)

if ebay_df is not None:
    frames.append(ebay_df)

if frames:

    final_df = pd.concat(frames, ignore_index=True)

    final_df["sort_date"] = pd.to_datetime(
        final_df["Data ordine"], format="%d/%m/%Y", errors="coerce"
    )

    final_df = final_df.sort_values("sort_date").drop(columns=["sort_date"])

    st.success("Elaborazione completata!")
    st.dataframe(final_df)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Orders")

    st.download_button(
        "⬇️ Scarica Excel finale",
        data=output.getvalue(),
        file_name="orders_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
