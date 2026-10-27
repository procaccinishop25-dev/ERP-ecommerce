"""Multi Marketplace Processor — Streamlit, senza Supabase.

Mappatura SKU opzionale tramite prodotti.csv/prodotti.xlsx nella cartella dell'app,
oppure caricamento di un file dalla barra laterale.
"""

from io import BytesIO
from pathlib import Path
import re

import pandas as pd

COLS = [
    "Data ordine",
    "Marketplace",
    "Paese (Mercato)",
    "Order ID (Codice Market)",
    "Prodotto",
    "Quantità ordinata",
    "Fatturato (Lordo)",
    "Fee (€)",
    "Log",
]


def read_table(file_or_path, filename=None):
    """Legge XLSX, CSV e TXT anche con separatori/encoding diversi."""
    if isinstance(file_or_path, (str, Path)):
        path = Path(file_or_path)
        filename = filename or path.name
        content = path.read_bytes()
    else:
        filename = filename or getattr(file_or_path, "name", "file.csv")
        content = file_or_path.getvalue() if hasattr(file_or_path, "getvalue") else file_or_path.read()

    if not content:
        raise ValueError(f"Il file {filename} è vuoto")

    if str(filename).lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(content), dtype=str)
    else:
        error = None
        for encoding in ("utf-8-sig", "utf-16", "cp1252"):
            try:
                df = pd.read_csv(
                    BytesIO(content),
                    sep=None,
                    engine="python",
                    encoding=encoding,
                    dtype=str,
                    keep_default_na=False,
                )
                break
            except (UnicodeError, pd.errors.ParserError, ValueError) as exc:
                error = exc
        else:
            raise ValueError(f"Impossibile leggere {filename}: {error}")

    df.columns = df.columns.astype(str).str.replace("\ufeff", "", regex=False).str.strip()
    return df


def require_columns(df, columns, label):
    absent = [c for c in columns if c not in df.columns]
    if absent:
        raise ValueError(f"{label}: colonne mancanti: {', '.join(absent)}. Colonne lette: {', '.join(df.columns[:12])}")


def find_col(df, *terms):
    for term in terms:
        for c in df.columns:
            if term.lower() in c.lower():
                return c
    return None


def normalize_id(x):
    if x is None or pd.isna(x):
        return ""
    return (
        str(x)
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("–", "-")
        .replace("−", "-")
        .replace("\xa0", "")
        .replace(" ", "")
        .strip()
    )


def normalize_code(x):
    code = normalize_id(x)
    return re.sub(r"\.0$", "", code).upper()


def extract_code(sku):
    sku = str(sku).strip()
    return sku.split("_")[1] if "_" in sku else sku


def add_row_log(log, msg):
    if not msg:
        return log if log else "OK"
    return msg if not log or log == "OK" or pd.isna(log) else f"{log} | {msg}"


def load_product_map(file_or_path):
    products = read_table(file_or_path)
    require_columns(products, ["codice", "nome_prodotto"], "Mappatura prodotti")
    products["codice"] = products["codice"].apply(normalize_code)
    products["nome_prodotto"] = products["nome_prodotto"].fillna("").astype(str).str.strip()
    products = products[(products["codice"] != "") & (products["nome_prodotto"] != "")]
    products = products.drop_duplicates(subset="codice", keep="last")
    return dict(zip(products["codice"], products["nome_prodotto"]))


def map_sku(sku, product_map):
    if sku is None or pd.isna(sku) or not str(sku).strip():
        return "", "SKU mancante"
    code = normalize_code(extract_code(sku))
    name = product_map.get(code)
    if name:
        return f"{name} - {code}", "OK"
    if not product_map:
        return str(sku), "Mappatura prodotti non caricata"
    return str(sku), "SKU non trovato nel mapping"


def to_float(value):
    """Interpreta 1.234,56 e 1,234.56, oltre a 1234.56 e 1234,56."""
    if value is None or pd.isna(value) or str(value).strip() == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    parenthesis_negative = raw.startswith("(") and raw.endswith(")")
    s = re.sub(r"[^\d,.-]", "", raw.replace("−", "-"))
    if not s or s == "-":
        return 0.0
    if "," in s and "." in s:
        decimal_sep = "," if s.rfind(",") > s.rfind(".") else "."
        group_sep = "." if decimal_sep == "," else ","
        s = s.replace(group_sep, "").replace(decimal_sep, ".")
    elif "," in s or "." in s:
        sep = "," if "," in s else "."
        parts = s.split(sep)
        # Più gruppi a tre cifre = separatore delle migliaia
        if len(parts) > 2 and all(len(p) == 3 for p in parts[1:]):
            s = "".join(parts)
        elif len(parts) == 2 and len(parts[1]) == 3 and len(parts[0].lstrip("-")) <= 3:
            s = "".join(parts)
        elif len(parts) > 2:
            s = "".join(parts[:-1]) + "." + parts[-1]
        else:
            s = s.replace(",", ".")
    try:
        number = float(s)
        return -abs(number) if parenthesis_negative else number
    except ValueError:
        return 0.0



def parse_local_dates(values):
    """Date ISO, gg/mm/aaaa e mesi abbreviati in italiano (es. 24 ott 2026)."""
    months = {
        "gennaio": "Jan", "gen": "Jan", "febbraio": "Feb", "feb": "Feb",
        "marzo": "Mar", "mar": "Mar", "aprile": "Apr", "apr": "Apr",
        "maggio": "May", "mag": "May", "giugno": "Jun", "giu": "Jun",
        "luglio": "Jul", "lug": "Jul", "agosto": "Aug", "ago": "Aug",
        "settembre": "Sep", "sett": "Sep", "set": "Sep",
        "ottobre": "Oct", "ott": "Oct", "novembre": "Nov", "nov": "Nov",
        "dicembre": "Dec", "dic": "Dec",
    }
    pattern = re.compile(r"\b(" + "|".join(sorted(months, key=len, reverse=True)) + r")\b", re.I)
    cleaned = values.astype(str).apply(
        lambda v: pattern.sub(lambda m: months[m.group(0).lower()], v)
    )
    return pd.to_datetime(cleaned, errors="coerce", dayfirst=True, format="mixed").dt.date

def map_country(val):
    if val is None or pd.isna(val):
        return ""
    v = str(val).strip().lower()
    countries = {
        "italy": "IT", "italia": "IT", "germany": "DE", "germania": "DE",
        "france": "FR", "francia": "FR", "spain": "ES", "spagna": "ES",
        "austria": "AT", "poland": "PL", "polonia": "PL",
        "czech republic": "CZ", "repubblica ceca": "CZ", "czechia": "CZ",
        "slovakia": "SK", "slovacchia": "SK", "portugal": "PT",
        "portogallo": "PT", "netherlands": "NL", "paesi bassi": "NL",
        "belgium": "BE", "belgio": "BE", "united kingdom": "GB",
        "regno unito": "GB", "ireland": "IE", "irlanda": "IE",
    }
    return countries.get(v, v.upper() if len(v) == 2 else v[:2].upper())


def allocate_fees(df, id_col, fee_col, weight_col):
    """Evita di conteggiare N volte le commissioni su ordini con N righe.
    Suddivide le fee in proporzione al fatturato delle singole righe.
    """
    weights = df[weight_col].abs().fillna(0.0)
    weight_totals = weights.groupby(df[id_col]).transform("sum")
    counts = df.groupby(id_col)[id_col].transform("size").replace(0, 1)
    shares = (weights / weight_totals.replace(0, float("nan"))).fillna(1 / counts)
    return df[fee_col].fillna(0.0) * shares


def process_amazon(orders_file, fees_file, product_map):
    orders = read_table(orders_file)
    require_columns(
        orders,
        ["amazon-order-id", "purchase-date", "sales-channel", "ship-country", "sku", "quantity", "item-price"],
        "Amazon ordini",
    )
    orders["amazon-order-id"] = orders["amazon-order-id"].apply(normalize_id)
    orders["_gross"] = orders["item-price"].apply(to_float)
    orders["_quantity"] = pd.to_numeric(orders["quantity"], errors="coerce").fillna(0)
    orders["_fee_total"] = float("nan")
    fees_loaded = fees_file is not None

    if fees_loaded:
        fees = read_table(fees_file)
        require_columns(fees, ["Numero di ordine", "Commissioni Amazon"], "Amazon commissioni")
        fees["Numero di ordine"] = fees["Numero di ordine"].apply(normalize_id)
        fees["_fee"] = fees["Commissioni Amazon"].apply(to_float).abs()
        fee_map = fees[fees["Numero di ordine"] != ""].groupby("Numero di ordine")["_fee"].sum()
        orders["_fee_total"] = orders["amazon-order-id"].map(fee_map)

    out = pd.DataFrame(index=orders.index)
    out["Data ordine"] = pd.to_datetime(orders["purchase-date"], errors="coerce", utc=True).dt.tz_convert("Europe/Rome").dt.date
    out["Marketplace"] = orders["sales-channel"].fillna("").astype(str).str.split(".", n=1).str[0]
    out["Paese (Mercato)"] = orders["ship-country"].apply(map_country)
    out["Order ID (Codice Market)"] = orders["amazon-order-id"]
    mapped = orders["sku"].apply(lambda sku: map_sku(sku, product_map))
    out["Prodotto"] = mapped.apply(lambda x: x[0])
    out["Log"] = mapped.apply(lambda x: x[1])
    out["Quantità ordinata"] = orders["_quantity"]
    out["Fatturato (Lordo)"] = orders["_gross"]
    out["Fee (€)"] = allocate_fees(orders, "amazon-order-id", "_fee_total", "_gross")
    if not fees_loaded:
        out["Log"] = out["Log"].apply(lambda log: add_row_log(log, "File commissioni Amazon non caricato"))
    else:
        missing = orders["_fee_total"].isna()
        out.loc[missing, "Log"] = out.loc[missing, "Log"].apply(
            lambda log: add_row_log(log, "Commissioni Amazon non trovate per questo ordine")
        )
    return out[COLS]


def process_temu(file, product_map):
    temu = read_table(file)
    date_col = find_col(temu, "data di acquisto", "purchase date", "data ordine")
    country_col = find_col(temu, "paese", "country")
    order_col = find_col(temu, "id ordine", "order id")
    sku_col = find_col(temu, "codice sku", "sku")
    qty_col = find_col(temu, "quantità", "quantity")
    title_col = find_col(temu, "nome dell'articolo", "nome articolo", "product name")
    if date_col is None or order_col is None or qty_col is None:
        raise ValueError("Temu: servono le colonne data di acquisto, ID ordine e quantità")

    out = pd.DataFrame(index=temu.index)
    out["Data ordine"] = parse_local_dates(temu[date_col])
    out["Marketplace"] = "Temu"
    out["Paese (Mercato)"] = temu[country_col].apply(map_country) if country_col else ""
    out["Order ID (Codice Market)"] = temu[order_col].apply(normalize_id)

    def resolve_product(row):
        sku = row[sku_col] if sku_col else ""
        title = row[title_col] if title_col else ""
        if pd.notna(sku) and str(sku).strip():
            return map_sku(sku, product_map)
        return (str(title) if pd.notna(title) else "", "SKU mancante, usato nome articolo")

    mapped = temu.apply(resolve_product, axis=1)
    out["Prodotto"] = mapped.apply(lambda x: x[0])
    out["Log"] = mapped.apply(lambda x: x[1])
    out["Quantità ordinata"] = pd.to_numeric(temu[qty_col], errors="coerce").fillna(0)

    def amount(col):
        return temu[col].apply(to_float) if col in temu.columns else pd.Series(0.0, index=temu.index)

    out["Fatturato (Lordo)"] = (
        amount("Totale prezzo base dopo lo sconto")
        + amount("Totale spedizione (imposte escluse)")
        + amount("Imposta sull'articolo")
        + amount("Imposta sulla spedizione")
    )
    out["Fee (€)"] = 0.0
    # Temu: 0 rappresenta commissioni non importate, non un costo realmente nullo.
    out["Log"] = out["Log"].apply(lambda log: add_row_log(log, "Commissioni Temu non disponibili nel file"))
    return out[COLS]


def process_ebay(orders_file, fees_file, product_map):
    orders = read_table(orders_file)
    require_columns(
        orders,
        ["Numero ordine", "Data vendita", "Paese dell'acquirente", "Quantità", "Costo totale"],
        "eBay ordini",
    )
    orders["Numero ordine"] = orders["Numero ordine"].apply(normalize_id)
    orders["_gross"] = orders["Costo totale"].apply(to_float)
    orders["_fee_total"] = float("nan")
    fees_loaded = fees_file is not None

    if fees_loaded:
        fees = read_table(fees_file)
        fee_components = [
            "Commissione sul valore finale - fissa",
            "Commissione sul valore finale - variabile",
            "Tariffa per l'adeguamento normativo",
        ]
        require_columns(fees, ["Numero ordine", *fee_components], "eBay commissioni")
        fees["Numero ordine"] = fees["Numero ordine"].apply(normalize_id)
        fees["_fee"] = sum((fees[col].apply(to_float).abs() for col in fee_components))
        fee_map = fees[fees["Numero ordine"] != ""].groupby("Numero ordine")["_fee"].sum()
        orders["_fee_total"] = orders["Numero ordine"].map(fee_map)

    out = pd.DataFrame(index=orders.index)
    out["Data ordine"] = parse_local_dates(orders["Data vendita"])
    out["Marketplace"] = "eBay"
    out["Paese (Mercato)"] = orders["Paese dell'acquirente"].apply(map_country)
    out["Order ID (Codice Market)"] = orders["Numero ordine"]

    def resolve_product(row):
        sku = row.get("Etichetta personalizzata", "")
        title = row.get("Titolo", "")
        if pd.notna(sku) and str(sku).strip():
            return map_sku(sku, product_map)
        return (str(title) if pd.notna(title) else "", "SKU mancante, usato titolo")

    mapped = orders.apply(resolve_product, axis=1)
    out["Prodotto"] = mapped.apply(lambda x: x[0])
    out["Log"] = mapped.apply(lambda x: x[1])
    out["Quantità ordinata"] = pd.to_numeric(orders["Quantità"], errors="coerce").fillna(0)
    out["Fatturato (Lordo)"] = orders["_gross"]
    out["Fee (€)"] = allocate_fees(orders, "Numero ordine", "_fee_total", "_gross")
    if not fees_loaded:
        out["Log"] = out["Log"].apply(lambda log: add_row_log(log, "File commissioni eBay non caricato"))
    else:
        missing = orders["_fee_total"].isna()
        out.loc[missing, "Log"] = out.loc[missing, "Log"].apply(
            lambda log: add_row_log(log, "Commissioni eBay non trovate per questo ordine")
        )
    return out[COLS]


def make_excel(final_df):
    out = BytesIO()
    export_df = final_df.copy()
    export_df["Data ordine"] = export_df["Data ordine"].apply(
        lambda d: d.isoformat() if pd.notna(d) and hasattr(d, "isoformat") else ""
    )
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Orders")
        sheet = writer.sheets["Orders"]
        sheet.freeze_panes(1, 0)
        sheet.autofilter(0, 0, len(export_df), len(COLS) - 1)
        sheet.set_column("A:A", 16)
        sheet.set_column("B:C", 17)
        sheet.set_column("D:D", 31)
        sheet.set_column("E:E", 55)
        sheet.set_column("F:F", 20)
        currency_format = writer.book.add_format({"num_format": '#,##0.00 "€"'})
        sheet.set_column("G:H", 19, currency_format)
        sheet.set_column("I:I", 65)
    out.seek(0)
    return out.getvalue()


def main():
    import streamlit as st

    st.set_page_config(page_title="Multi Marketplace Processor", page_icon="📦", layout="wide")
    st.title("📦 Multi Marketplace Processor")
    st.caption("Amazon, Temu ed eBay • Nessun database e nessuna credenziale richiesta")

    with st.sidebar:
        st.header("📚 Mappatura prodotti (opzionale)")
        st.write("Carica un CSV/Excel con le colonne **codice** e **nome_prodotto**.")
        map_file = st.file_uploader("File prodotti", type=["csv", "xlsx"], key="map_products")

    product_map = {}
    source = map_file
    if source is None:
        source = next((p for p in (Path("prodotti.xlsx"), Path("prodotti.csv")) if p.is_file()), None)
    if source is not None:
        try:
            product_map = load_product_map(source)
            st.sidebar.success(f"{len(product_map)} codici prodotto caricati")
        except Exception as exc:
            st.sidebar.error(f"Errore mappatura: {exc}")
    else:
        st.sidebar.info("Senza mappatura l'app funziona comunque: mantiene gli SKU originali nel risultato.")

    with st.expander("📄 Carica i file dei marketplace", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("Amazon")
            amazon_orders = st.file_uploader("Ordini", type=["txt", "csv", "xlsx"], key="amazon_orders")
            amazon_fees = st.file_uploader("Commissioni", type=["csv", "xlsx"], key="amazon_fees")
        with col2:
            st.subheader("Temu")
            temu_file = st.file_uploader("Ordini Temu", type=["txt", "csv", "xlsx"], key="temu")
        with col3:
            st.subheader("eBay")
            ebay_orders = st.file_uploader("Ordini", type=["txt", "csv", "xlsx"], key="ebay_orders")
            ebay_fees = st.file_uploader("Commissioni", type=["txt", "csv", "xlsx"], key="ebay_fees")

    if not any([amazon_orders, temu_file, ebay_orders]):
        st.info("Carica almeno un file ordini per iniziare. I file delle commissioni sono facoltativi, ma consigliati.")
        return

    if st.button("⚙️ Elabora file", type="primary"):
        frames = []
        for name, present, action in [
            ("Amazon", amazon_orders, lambda: process_amazon(amazon_orders, amazon_fees, product_map)),
            ("Temu", temu_file, lambda: process_temu(temu_file, product_map)),
            ("eBay", ebay_orders, lambda: process_ebay(ebay_orders, ebay_fees, product_map)),
        ]:
            if present:
                try:
                    frame = action()
                    frames.append(frame)
                    st.success(f"{name}: {len(frame)} righe elaborate")
                except Exception as exc:
                    st.error(f"Errore nel file {name}: {exc}")

        if not frames:
            return

        final_df = pd.concat(frames, ignore_index=True)
        final_df["_sort_date"] = pd.to_datetime(final_df["Data ordine"], errors="coerce")
        final_df = final_df.sort_values("_sort_date", kind="stable").drop(columns="_sort_date").reset_index(drop=True)
        st.subheader("📊 Risultato")
        st.dataframe(final_df, use_container_width=True, hide_index=True)
        st.caption("Le fee non disponibili sono riportate come 0 nel file, con un avviso nella colonna Log. Non considerarle costi nulli.")
        st.download_button(
            "⬇️ Scarica Excel finale",
            data=make_excel(final_df),
            file_name="orders_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


if __name__ == "__main__":
    main()
