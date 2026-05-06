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
ebay_file = st.file_uploader("📄 EBAY FILE", type=["csv", "txt", "xlsx"])

# -------------------------
# AMAZON UTILS
# -------------------------
def extract_code(sku):
    return str(sku).split("_")[1] if "_" in str(sku) else sku

def map_sku(original_sku):
    code = extract_code(original_sku)
    return f"{product_map.get(code)} - {code}" if product_map.get(code) else original_sku

def clean_marketplace(val):
    return str(val).split(".")[0] if pd.notna(val) else val

# -------------------------
# TEMU UTILS
# -------------------------
def find_col(df, keyword):
    for c in df.columns:
        if keyword.lower() in c.lower():
            return c
    return None

def to_float(x):
    try:
        return float(str(x).replace(",", ".").replace("€", "").strip())
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
# TEMU DATE FIX
# -------------------------
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
        if f" {it} " in x:
            x = x.replace(it, en)

    return pd.to_datetime(x, errors="coerce")

# =========================================================
# AMAZON PROCESS
# =========================================================
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
        "fee"
    ]].rename(columns={
        "ship-country": "Paese (Mercato)",
        "amazon-order-id": "Order ID (Codice Market)",
        "quantity": "Quantità ordinata",
        "item-price": "Fatturato (Lordo)",
        "fee": "Fee (€)"
    })

# =========================================================
# TEMU PROCESS
# =========================================================
temu_df = None

if temu_file:

    if temu_file.name.endswith(".xlsx"):
        temu = pd.read_excel(temu_file)
    else:
        temu = pd.read_csv(temu_file, sep="\t", encoding="utf-8", on_bad_lines="skip")

    temu.columns = (
        temu.columns
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\n", " ", regex=True)
        .str.strip()
    )

    date_col = find_col(temu, "data di acquisto")
    country_col = find_col(temu, "paese")
    order_col = find_col(temu, "id ordine")
    sku_col = find_col(temu, "codice sku")
    qty_col = find_col(temu, "quantità")

    if date_col is None or country_col is None or order_col is None:
        st.error("❌ Colonne Temu non trovate")
        st.write(temu.columns.tolist())
        st.stop()

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
        if pd.notna(sku) and str(sku).strip() != "":
            return sku
        return name

    t["Prodotto"] = temu.apply(get_product, axis=1)

    t["Quantità ordinata"] = pd.to_numeric(
        temu[qty_col],
        errors="coerce"
    ).fillna(0)

    def safe_col(df, col):
        return df[col].apply(to_float) if col in df.columns else 0

    t["Fatturato (Lordo)"] = (
        safe_col(temu, "Totale prezzo base dopo lo sconto")
        + safe_col(temu, "Totale spedizione (imposte escluse)")
        + safe_col(temu, "Imposta sull'articolo")
        + safe_col(temu, "Imposta sulla spedizione")
    )

    t["Fee (€)"] = 0.0

    temu_df = t

# =========================================================
# EBAY PROCESS (COMPLETO + ADS FIX)
# =========================================================
ebay_df = None

if ebay_file:

    if ebay_file.name.endswith(".xlsx"):
        ebay = pd.read_excel(ebay_file)
    else:
        ebay = pd.read_csv(ebay_file, sep="\t", encoding="utf-8", on_bad_lines="skip")

    ebay.columns = (
        ebay.columns
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\n", " ", regex=True)
        .str.strip()
    )

    def map_country_ebay(val):
        if pd.isna(val):
            return ""
        val = str(val).lower()
        return {
            "italia": "IT",
            "italy": "IT",
            "germany": "DE",
            "deutschland": "DE",
            "france": "FR",
            "spain": "ES"
        }.get(val, val[:2].upper())

    def parse_ebay_date(x):
        if pd.isna(x):
            return pd.NaT

        x = str(x)

        mesi = {
            "gen": "Jan","feb": "Feb","mar": "Mar","apr": "Apr",
            "mag": "May","giu": "Jun","lug": "Jul","ago": "Aug",
            "set": "Sep","ott": "Oct","nov": "Nov","dic": "Dec"
        }

        for it, en in mesi.items():
            x = re.sub(rf"\b{it}\b", en, x)

        x = re.sub(r"CEST.*", "", x).strip()

        return pd.to_datetime(x, errors="coerce")

    # ---------------- ORDINI ----------------
    orders = ebay[
        ~ebay["Tipo di imposte riscosse e versate da eBay"]
        .fillna("")
        .str.contains("Tariffa Inserzioni sponsorizzate", na=False)
    ].copy()

    orders["Data ordine"] = pd.to_datetime(
        orders["Data vendita"].apply(parse_ebay_date),
        errors="coerce"
    ).dt.strftime("%d/%m/%Y")

    def detect_marketplace(order_id):
        if str(order_id).startswith("PO-098"):
            return "Temu"
        return "eBay"

    orders["Marketplace"] = orders["Numero ordine"].apply(detect_marketplace)
    orders["Paese (Mercato)"] = orders["Paese dell'acquirente"].apply(map_country_ebay)
    orders["Order ID (Codice Market)"] = orders["Numero ordine"]

    def get_product(row):
        sku = row.get("Etichetta personalizzata")
        title = row.get("Titolo")

        if pd.notna(sku) and str(sku).strip():
            return sku
        return title

    orders["Prodotto"] = orders.apply(get_product, axis=1)

    orders["Quantità ordinata"] = pd.to_numeric(
        orders["Quantità"],
        errors="coerce"
    ).fillna(0)

    orders["Fatturato (Lordo)"] = orders["Costo totale"].apply(to_float)

    def safe_sum(df, cols):
        return sum(df[c].apply(to_float) if c in df.columns else 0 for c in cols)

    orders["Fee (€)"] = safe_sum(orders, [
        "Commissione sul valore finale - fissa",
        "Commissione sul valore finale - variabile",
        "Tariffa per l'adeguamento normativo"
    ])

    # ---------------- ADS ----------------
    ads = ebay[
        ebay["Tipo di imposte riscosse e versate da eBay"]
        .fillna("")
        .str.contains("Tariffa Inserzioni sponsorizzate", na=False)
    ]

    if not ads.empty:

        ads_grouped = ads.groupby("Numero ordine", as_index=False).agg({
            "Data vendita": "first",
            "Paese dell'acquirente": "first",
            "Costo totale": "sum"
        })

        ads_grouped["Data ordine"] = pd.to_datetime(
            ads_grouped["Data vendita"].apply(parse_ebay_date),
            errors="coerce"
        ).dt.strftime("%d/%m/%Y")

        ads_grouped["Marketplace"] = "eBay"
        ads_grouped["Paese (Mercato)"] = ads_grouped["Paese dell'acquirente"].apply(map_country_ebay)
        ads_grouped["Order ID (Codice Market)"] = ads_grouped["Numero ordine"]
        ads_grouped["Prodotto"] = "Tariffa Inserzioni Sponsorizzate"
        ads_grouped["Quantità ordinata"] = 0
        ads_grouped["Fatturato (Lordo)"] = 0
        ads_grouped["Fee (€)"] = ads_grouped["Costo totale"].apply(to_float)

        ads_grouped = ads_grouped[[
            "Data ordine","Marketplace","Paese (Mercato)",
            "Order ID (Codice Market)","Prodotto",
            "Quantità ordinata","Fatturato (Lordo)","Fee (€)"
        ]]

        ebay_df = pd.concat([orders, ads_grouped], ignore_index=True)
    else:
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
    final_df = final_df.sort_values("Data ordine", ascending=True)

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
