import streamlit as st
import pandas as pd
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


# -------------------------
# AMAZON
# -------------------------
def extract_code(sku):
    return str(sku).split("_")[1] if "_" in str(sku) else sku


def map_sku(original_sku):
    code = extract_code(original_sku)
    return f"{product_map.get(code)} - {code}" if product_map.get(code) else original_sku


def clean_marketplace(val):
    return str(val).split(".")[0] if pd.notna(val) else val


# -------------------------
# TEMU FIX FUNZIONI
# -------------------------
def to_float(x):
    try:
        return float(str(x).replace(",", "."))
    except:
        return 0.0


def temu_gross(row):
    return (
        to_float(row["Totale prezzo base dopo lo sconto"])
        + to_float(row["Totale spedizione (imposte escluse)"])
        + to_float(row["Imposta sull'articolo"])
        + to_float(row["Imposta sulla spedizione"])
    )


def map_country(val):
    if pd.isna(val):
        return ""
    val = str(val).strip().lower()
    return {
        "italy": "IT",
        "germany": "DE",
        "france": "FR",
        "spain": "ES"
    }.get(val, val[:2].upper())


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


# -------------------------
# TEMU PROCESS (FIX DEFINITIVO)
# -------------------------
temu_df = None

if temu_file:

    if temu_file.name.endswith(".xlsx"):
        temu = pd.read_excel(temu_file)
    else:
        temu = pd.read_csv(temu_file, sep="\t", encoding="utf-8", on_bad_lines="skip")

    # 🔥 FIX COLONNE
    temu.columns = (
        temu.columns
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\n", " ", regex=True)
        .str.strip()
    )

    t = pd.DataFrame()

    # -------------------------
    # DATA ORDINE (FIX DEFINITIVO)
    # -------------------------
    t["Data ordine"] = pd.to_datetime(
        temu["data di acquisto"],
        errors="coerce"
    ).dt.strftime("%d/%m/%Y")

    # -------------------------
    # MARKETPLACE
    # -------------------------
    t["Marketplace"] = "Temu"

    # -------------------------
    # PAESE
    # -------------------------
    t["Paese (Mercato)"] = temu["Paese di spedizione"].apply(map_country)

    # -------------------------
    # ORDER ID
    # -------------------------
    t["Order ID (Codice Market)"] = temu["ID Ordine"]

    # -------------------------
    # PRODOTTO
    # -------------------------
    def get_product(row):
        sku = row["Codice SKU"]
        name = row["nome dell'articolo"]

        if pd.notna(sku) and str(sku).strip() != "":
            return sku
        return name

    t["Prodotto"] = temu.apply(get_product, axis=1)

    # -------------------------
    # QUANTITÀ
    # -------------------------
    t["Quantità ordinata"] = pd.to_numeric(
        temu["quantità acquistata"],
        errors="coerce"
    ).fillna(0)

    # -------------------------
    # FATTURATO (FIX REALE)
    # -------------------------
    t["Fatturato (Lordo)"] = temu.apply(temu_gross, axis=1)

    # -------------------------
    # FEE
    # -------------------------
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
    # EXPORT EXCEL
    # -------------------------
    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Orders")

    st.download_button(
        "⬇️ Scarica Excel finale",
        data=output.getvalue(),
        file_name="orders_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
