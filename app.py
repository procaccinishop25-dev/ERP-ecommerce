import streamlit as st
import pandas as pd
import re
from supabase import create_client
from io import BytesIO

# =========================================================
# SUPABASE
# =========================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📦 Multi Marketplace Processor")

# =========================================================
# PRODOTTI SUPABASE
# =========================================================
@st.cache_data
def load_products():
    res = supabase.table("prodotti").select("codice, nome_prodotto").execute()
    return pd.DataFrame(res.data)

products_df = load_products()
product_map = dict(zip(products_df["codice"], products_df["nome_prodotto"]))

# =========================================================
# UPLOAD FILE
# =========================================================
orders_file = st.file_uploader("📄 Amazon ORDINI", type=["csv", "txt"])
comm_file = st.file_uploader("📄 Amazon COMMISSIONI", type=["csv", "txt"])
temu_file = st.file_uploader("📄 TEMU FILE", type=["csv", "txt", "xlsx"])
ebay_orders_file = st.file_uploader("📄 EBAY ORDINI", type=["csv", "txt", "xlsx"])
ebay_comm_file = st.file_uploader("📄 EBAY COMMISSIONI", type=["csv", "txt", "xlsx"])

# =========================================================
# UTILS
# =========================================================
def extract_code(sku):
    return str(sku).split("_")[1] if "_" in str(sku) else sku

def map_sku(original_sku):
    code = extract_code(original_sku)
    return f"{product_map.get(code)} - {code}" if product_map.get(code) else original_sku

def clean_marketplace(val):
    return str(val).split(".")[0] if pd.notna(val) else val

def to_float(x):
    try:
        return float(str(x).replace(",", ".").replace("€", "").replace("--", "0").strip())
    except:
        return 0.0

def find_col(df, keyword):
    for c in df.columns:
        if keyword.lower() in c.lower():
            return c
    return None

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

# =========================================================
# TEMU DATE
# =========================================================
def parse_temu_date(x):
    if pd.isna(x):
        return pd.NaT

    x = str(x)
    x = re.sub(r"CEST.*", "", x).strip()

    mesi = {
        "gen": "Jan","feb": "Feb","mar": "Mar","apr": "Apr",
        "mag": "May","giu": "Jun","lug": "Jul","ago": "Aug",
        "set": "Sep","ott": "Oct","nov": "Nov","dic": "Dec"
    }

    for it, en in mesi.items():
        x = re.sub(rf"\b{it}\b", en, x)

    return pd.to_datetime(x, errors="coerce")

# =========================================================
# AMAZON
# =========================================================
amazon_df = None

if orders_file and comm_file:

    orders = pd.read_csv(orders_file, sep="\t")
    comm = pd.read_csv(comm_file, sep=",")

    comm = comm.rename(columns={
        "Numero di ordine": "amazon-order-id"
    })

    df = orders.merge(comm, on="amazon-order-id", how="left")

    df["Data ordine"] = pd.to_datetime(
        df["purchase-date"], errors="coerce", utc=True
    ).dt.strftime("%d/%m/%Y")

    df["Marketplace"] = df["sales-channel"].apply(clean_marketplace)
    df["Prodotto"] = df["sku"].apply(map_sku)

    amazon_df = df[[
        "Data ordine",
        "Marketplace",
        "ship-country",
        "amazon-order-id",
        "Prodotto",
        "quantity",
        "item-price",
        "Commissioni Amazon"
    ]].rename(columns={
        "ship-country": "Paese (Mercato)",
        "amazon-order-id": "Order ID (Codice Market)",
        "quantity": "Quantità ordinata",
        "item-price": "Fatturato (Lordo)",
        "Commissioni Amazon": "Fee (€)"
    })

# =========================================================
# TEMU
# =========================================================
temu_df = None

if temu_file:

    if temu_file.name.endswith(".xlsx"):
        temu = pd.read_excel(temu_file)
    else:
        temu = pd.read_csv(temu_file, sep="\t", encoding="utf-8", on_bad_lines="skip")

    temu.columns = temu.columns.str.strip()

    date_col = find_col(temu, "data di acquisto")
    country_col = find_col(temu, "paese")
    order_col = find_col(temu, "id ordine")
    sku_col = find_col(temu, "codice sku")
    qty_col = find_col(temu, "quantità")

    t = pd.DataFrame()

    t["Data ordine"] = pd.to_datetime(
        temu[date_col].astype(str).apply(parse_temu_date),
        errors="coerce"
    ).dt.strftime("%d/%m/%Y")

    t["Marketplace"] = "Temu"
    t["Paese (Mercato)"] = temu[country_col].apply(map_country)
    t["Order ID (Codice Market)"] = temu[order_col]

    def get_product(row):
        sku = row.get(sku_col)
        name = row.get("nome dell'articolo")
        return sku if pd.notna(sku) and str(sku).strip() else name

    t["Prodotto"] = temu.apply(get_product, axis=1)

    t["Quantità ordinata"] = pd.to_numeric(temu[qty_col], errors="coerce").fillna(0)

    def safe_col(col):
        return temu[col].apply(to_float) if col in temu.columns else 0

    t["Fatturato (Lordo)"] = (
        safe_col("Totale prezzo base dopo lo sconto")
        + safe_col("Totale spedizione (imposte escluse)")
        + safe_col("Imposta sull'articolo")
        + safe_col("Imposta sulla spedizione")
    )

    t["Fee (€)"] = 0.0

    temu_df = t

# =========================================================
# EBAY (FIX DEFINITIVO)
# =========================================================
ebay_df = None

if ebay_orders_file and ebay_comm_file:

    orders = pd.read_excel(ebay_orders_file) if ebay_orders_file.name.endswith(".xlsx") else pd.read_csv(ebay_orders_file, sep="\t", encoding="utf-8", on_bad_lines="skip")
    comm = pd.read_excel(ebay_comm_file) if ebay_comm_file.name.endswith(".xlsx") else pd.read_csv(ebay_comm_file, sep="\t", encoding="utf-8", on_bad_lines="skip")

    orders.columns = orders.columns.str.strip()
    comm.columns = comm.columns.str.strip()

    # ---------------- ORDERS ----------------
    def parse_ebay_date(x):
        if pd.isna(x):
            return pd.NaT
        x = str(x)
        x = re.sub(r"CEST.*", "", x)
        return pd.to_datetime(x, errors="coerce")

    orders["Data ordine"] = pd.to_datetime(
        orders["Data vendita"].apply(parse_ebay_date),
        errors="coerce"
    ).dt.strftime("%d/%m/%Y")

    def map_country_ebay(val):
        if pd.isna(val):
            return ""
        return {
            "italia": "IT",
            "italy": "IT",
            "germany": "DE",
            "france": "FR",
            "spain": "ES"
        }.get(str(val).lower(), str(val)[:2].upper())

    orders["Marketplace"] = orders["Numero ordine"].apply(lambda x: "Temu" if str(x).startswith("PO-098") else "eBay")
    orders["Paese (Mercato)"] = orders["Paese dell'acquirente"].apply(map_country_ebay)
    orders["Order ID (Codice Market)"] = orders["Numero ordine"]

    orders["Prodotto"] = orders.apply(lambda r: r.get("Etichetta personalizzata") or r.get("Titolo"), axis=1)

    orders["Quantità ordinata"] = pd.to_numeric(orders["Quantità"], errors="coerce").fillna(0)

    orders["Fatturato (Lordo)"] = orders["Costo totale"].apply(to_float)

    # ---------------- FEES FIX ----------------
    comm_cols = [
        "Commissione sul valore finale - fissa",
        "Commissione sul valore finale - variabile",
        "Tariffa per l'adeguamento normativo",
        "Costo totale"
    ]

    for c in comm_cols:
        if c in comm.columns:
            comm[c] = comm[c].apply(to_float)
        else:
            comm[c] = 0

    comm["fee_row"] = comm[comm_cols].sum(axis=1)

    fees = comm.groupby("Numero ordine", as_index=False)["fee_row"].sum()
    fees = fees.rename(columns={"fee_row": "Fee (€)"})

    orders = orders.merge(fees, left_on="Numero ordine", right_on="Numero ordine", how="left")
    orders["Fee (€)"] = orders["Fee (€)"].fillna(0)

    ebay_df = orders

# =========================================================
# MERGE FINALE
# =========================================================
frames = []

if amazon_df is not None:
    frames.append(amazon_df)

if temu_df is not None:
    frames.append(temu_df)

if ebay_df is not None:
    frames.append(ebay_df)

if frames:

    final_df = pd.concat(frames, ignore_index=True)
    final_df = final_df.sort_values("Data ordine")

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
