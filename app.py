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
    name = product_map.get(code)
    return f"{name} - {code}" if name else original_sku

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
# ERROR BUILDER
# -------------------------
def build_errors(data):
    errors = []

    if data.get("sku_ok") is False:
        errors.append("SKU non trovato")

    if data.get("fee_ok") is False:
        errors.append("Fee mancante")

    if data.get("price_ok") is False:
        errors.append("Prezzo non valido")

    if data.get("qty_ok") is False:
        errors.append("Quantità non valida")

    if data.get("date_ok") is False:
        errors.append("Data non valida")

    return "OK" if len(errors) == 0 else " | ".join(errors)

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
    ).dt.tz_convert("Europe/Rome").dt.date

    df["Prodotto"] = df["sku"].apply(map_sku)

    df["Errori riga"] = df.apply(lambda r: build_errors({
        "sku_ok": pd.notna(r["sku"]),
        "fee_ok": pd.notna(r["fee"]),
        "price_ok": pd.notna(r["item-price"]),
        "qty_ok": pd.notna(r["quantity"]),
        "date_ok": pd.notna(r["Data ordine"])
    }), axis=1)

    amazon_df = df[[
        "Data ordine",
        "sku",
        "Prodotto",
        "quantity",
        "item-price",
        "fee",
        "amazon-order-id",
        "Errori riga"
    ]].rename(columns={
        "amazon-order-id": "Order ID",
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

    def find_col(df, keyword):
        for c in df.columns:
            if keyword.lower() in c.lower():
                return c
        return None

    date_col = find_col(temu, "data di acquisto")
    sku_col = find_col(temu, "codice sku")
    qty_col = find_col(temu, "quantità")

    t = pd.DataFrame()

    t["Data ordine"] = pd.to_datetime(temu[date_col], errors="coerce").dt.date

    def get_product(row):
        sku = row.get(sku_col)
        if pd.notna(sku):
            return map_sku(sku)
        return row.get("nome dell'articolo")

    t["Prodotto"] = temu.apply(get_product, axis=1)

    t["Errori riga"] = t.apply(lambda r: build_errors({
        "sku_ok": pd.notna(r.get("Prodotto")),
        "fee_ok": True,
        "price_ok": True,
        "qty_ok": pd.notna(temu.loc[r.name, qty_col]),
        "date_ok": pd.notna(r["Data ordine"])
    }), axis=1)

    t["Marketplace"] = "Temu"
    t["Quantità ordinata"] = pd.to_numeric(temu[qty_col], errors="coerce").fillna(0)

    t["Fatturato (Lordo)"] = 0
    t["Fee (€)"] = 0

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

    ebay_fee["fee_totale"] = ebay_fee.fillna(0).select_dtypes(include="number").sum(axis=1)

    df = ebay_orders.merge(
        ebay_fee.groupby("Numero ordine")["fee_totale"].sum().reset_index(),
        on="Numero ordine",
        how="left"
    )

    e = pd.DataFrame()

    e["Data ordine"] = pd.to_datetime(df["Data vendita"], errors="coerce").dt.date

    e["Prodotto"] = df.get("Titolo")

    e["Errori riga"] = e.apply(lambda r: build_errors({
        "sku_ok": True,
        "fee_ok": pd.notna(df.loc[r.name, "fee_totale"]),
        "price_ok": pd.notna(df.loc[r.name, "Costo totale"]),
        "qty_ok": pd.notna(df.loc[r.name, "Quantità"]),
        "date_ok": pd.notna(r["Data ordine"])
    }), axis=1)

    e["Marketplace"] = "eBay"
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

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Orders")

    output.seek(0)

    st.download_button(
        "⬇️ Scarica Excel finale",
        data=output,
        file_name="orders_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
