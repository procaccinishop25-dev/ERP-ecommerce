import streamlit as st
import pandas as pd
from supabase import create_client

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


# -------------------------
# FUNZIONI AMAZON
# -------------------------
def extract_code(sku):
    return str(sku).split("_")[1] if "_" in str(sku) else sku


def map_sku(original_sku):
    code = extract_code(original_sku)
    return f"{product_map.get(code)} - {code}" if product_map.get(code) else original_sku


def clean_marketplace(val):
    return str(val).split(".")[0] if pd.notna(val) else val


# -------------------------
# TEMU FUNCTIONS
# -------------------------
def parse_temu_date(date_str):
    dt = pd.to_datetime(date_str, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return ""
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
    return name if pd.notna(name) else sku


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

if orders_file and comm_file:

    orders = pd.read_csv(orders_file, sep="\t")
    comm = pd.read_csv(comm_file, sep=",")

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

    df["Prodotto"] = df["sku"].apply(map_sku)

    amazon_df = df[[
        "Data ordine",
        "Marketplace",
        "ship-country",
        "amazon-order-id",
        "Prodotto",
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
# TEMU PROCESS
# -------------------------
temu_df = None

if temu_file:

    if temu_file.name.endswith(".xlsx"):
        temu = pd.read_excel(temu_file)
    else:
        temu = pd.read_csv(temu_file, sep="\t", encoding="utf-8", on_bad_lines="skip")

    temu.columns = temu.columns.str.strip().str.lower()

    t = pd.DataFrame()

    # DATA
    date_col = [c for c in temu.columns if "acquisto" in c][0]
    t["Data ordine"] = temu[date_col].apply(parse_temu_date)

    # MARKETPLACE
    t["Marketplace"] = "Temu"

    # PAESE
    country_col = [c for c in temu.columns if "spedizione" in c][0]
    t["Paese (Mercato)"] = temu[country_col].apply(map_country)

    # ORDER ID
    order_col = [c for c in temu.columns if "id ordine" in c][0]
    t["Order ID (Codice Market)"] = temu[order_col]

    # PRODOTTO
    t["Prodotto"] = temu.apply(temu_product, axis=1)

    # QUANTITÀ
    qty_col = [c for c in temu.columns if "quantità" in c][0]
    t["Quantità ordinata"] = temu[qty_col]

    # FATTURATO (CALCOLO COMPLETO)
    t["Fatturato (Lordo)"] = temu.apply(temu_gross, axis=1)

    # FEE
    t["Fee (€)"] = 0.00

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

    final_df = final_df.sort_values("Data ordine", ascending=True)

    st.success("Elaborazione completata!")

    st.dataframe(final_df)

    # -------------------------
    # EXPORT EXCEL (NON CSV)
    # -------------------------
    from io import BytesIO

    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Orders")

    st.download_button(
        "⬇️ Scarica Excel finale",
        data=output.getvalue(),
        file_name="orders_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
