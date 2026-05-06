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

st.title("📦 ERP Multi Marketplace Stable")


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
amazon_orders = st.file_uploader("📄 Amazon ORDINI", type=["csv", "txt"])
amazon_comm = st.file_uploader("📄 Amazon COMMISSIONI", type=["csv", "txt"])
temu_file = st.file_uploader("📄 TEMU FILE", type=["csv", "txt", "xlsx"])


# -------------------------
# UTILS GLOBALI
# -------------------------
def normalize_columns(df):
    df.columns = (
        df.columns
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\n", " ", regex=True)
        .str.strip()
    )
    return df


def find_col(df, keyword):
    keyword = keyword.lower().strip()
    for c in df.columns:
        c_clean = str(c).lower().strip()
        if keyword in c_clean or c_clean in keyword:
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
# AMAZON
# -------------------------
def extract_code(sku):
    return str(sku).split("_")[1] if "_" in str(sku) else sku


def map_sku(original_sku):
    code = extract_code(original_sku)
    return f"{product_map.get(code)} - {code}" if product_map.get(code) else original_sku


amazon_df = None

if amazon_orders and amazon_comm:

    orders = pd.read_csv(amazon_orders, sep="\t")
    comm = pd.read_csv(amazon_comm, sep=",")

    comm = comm.rename(columns={
        "Numero di ordine": "amazon-order-id",
        "Commissioni Amazon": "fee"
    })

    df = orders.merge(comm, on="amazon-order-id", how="left")

    amazon_df = pd.DataFrame()

    amazon_df["Data ordine"] = pd.to_datetime(
        df["purchase-date"],
        errors="coerce",
        utc=True
    ).dt.strftime("%d/%m/%Y")

    amazon_df["Marketplace"] = df["sales-channel"]
    amazon_df["Order ID"] = df["amazon-order-id"]
    amazon_df["Paese"] = df["ship-country"]
    amazon_df["Prodotto"] = df["sku"].apply(map_sku)
    amazon_df["Quantità"] = df["quantity"]
    amazon_df["Fatturato"] = df["item-price"]
    amazon_df["Fee"] = df["fee"]


# -------------------------
# TEMU (STABILE DEFINITIVO)
# -------------------------
temu_df = None

if temu_file:

    try:
        if temu_file.name.endswith(".xlsx"):
            temu = pd.read_excel(temu_file)
        else:
            temu = pd.read_csv(temu_file, sep="\t", encoding="utf-8", on_bad_lines="skip")

        temu = normalize_columns(temu)

        # -------------------------
        # COLONNE DINAMICHE
        # -------------------------
        date_col = find_col(temu, "acquisto")
        country_col = find_col(temu, "paese")
        order_col = find_col(temu, "id ordine")
        sku_col = find_col(temu, "codice sku")
        qty_col = find_col(temu, "quantità")

        # 🔥 CONTROLLO SICUREZZA
        if not all([date_col, country_col, order_col, qty_col]):
            st.error("❌ File Temu non riconosciuto correttamente")
            st.write("Colonne trovate:", temu.columns.tolist())
            st.stop()

        # -------------------------
        # DATA TEMU FIX
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


        temu_df = pd.DataFrame()

        temu_df["Data ordine"] = temu[date_col].apply(parse_temu_date).dt.strftime("%d/%m/%Y")
        temu_df["Marketplace"] = "Temu"
        temu_df["Order ID"] = temu[order_col]
        temu_df["Paese"] = temu[country_col].apply(map_country)
        temu_df["Quantità"] = pd.to_numeric(temu[qty_col], errors="coerce").fillna(0)

        # -------------------------
        # PRODOTTO
        # -------------------------
        def get_product(row):
            sku = row.get(sku_col)
            name = row.get("nome dell'articolo")

            if pd.notna(sku) and str(sku).strip() != "":
                return sku
            return name

        temu_df["Prodotto"] = temu.apply(get_product, axis=1)

        # -------------------------
        # FATTURATO
        # -------------------------
        def get_col(keyword):
            for c in temu.columns:
                if keyword in c:
                    return c
            return None

        def safe(col):
            return temu[col].apply(to_float) if col else 0

        c1 = get_col("prezzo base dopo")
        c2 = get_col("spedizione")
        c3 = get_col("imposta sull'articolo")
        c4 = get_col("imposta sulla spedizione")

        temu_df["Fatturato"] = safe(c1) + safe(c2) + safe(c3) + safe(c4)

        temu_df["Fee"] = 0.0

    except Exception as e:
        st.error(f"Errore Temu: {e}")


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

    st.success("ERP generato correttamente")
    st.dataframe(final_df)

    # -------------------------
    # EXPORT EXCEL
    # -------------------------
    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Orders")

    st.download_button(
        "⬇️ Scarica Excel ERP",
        data=output.getvalue(),
        file_name="erp_orders.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
