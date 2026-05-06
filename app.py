# -------------------------
# EBAY PROCESS
# -------------------------
ebay_df = None

if ebay_file:

    if ebay_file.name.endswith(".xlsx"):
        ebay = pd.read_excel(ebay_file)
    else:
        ebay = pd.read_csv(ebay_file, sep="\t", encoding="utf-8", on_bad_lines="skip")

    # pulizia colonne
    ebay.columns = (
        ebay.columns
        .str.replace("\ufeff", "", regex=True)
        .str.replace("\n", " ", regex=True)
        .str.strip()
    )

    # -------------------------
    # FUNZIONE MAP PAESI
    # -------------------------
    def map_country_ebay(val):
        if pd.isna(val):
            return ""
        val = str(val).lower()

        mapping = {
            "italia": "IT",
            "italy": "IT",
            "germany": "DE",
            "deutschland": "DE",
            "france": "FR",
            "spain": "ES",
            "españa": "ES"
        }

        return mapping.get(val, val[:2].upper())

    # -------------------------
    # ORDINI (solo righe "Ordine")
    # -------------------------
    orders = ebay[ebay["Tipo di imposte riscosse e versate da eBay"].fillna("").str.lower().ne("tariffa inserzioni sponsorizzate con strategia generale")]

    # -------------------------
    # DATA ORDINE (italiana)
    # -------------------------
    def parse_ebay_date(x):
        if pd.isna(x):
            return pd.NaT

        x = str(x)

        mesi = {
            "gen": "Jan",
            "feb": "Feb",
            "mar": "Mar",
            "apr": "Apr",
            "mag": "May",
            "giu": "Jun",
            "lug": "Jul",
            "ago": "Aug",
            "set": "Sep",
            "ott": "Oct",
            "nov": "Nov",
            "dic": "Dec"
        }

        for it, en in mesi.items():
            x = re.sub(rf"\b{it}\b", en, x)

        x = re.sub(r"CEST.*", "", x).strip()

        return pd.to_datetime(x, errors="coerce")

    orders["Data ordine"] = pd.to_datetime(
        orders["Data vendita"].apply(parse_ebay_date),
        errors="coerce"
    ).dt.strftime("%d/%m/%Y")

    # -------------------------
    # MARKETPLACE (logica PO-098 = Temu)
    # -------------------------
    def detect_marketplace(order_id):
        if str(order_id).startswith("PO-098"):
            return "Temu"
        return "eBay"

    orders["Marketplace"] = orders["Numero ordine"].apply(detect_marketplace)

    # -------------------------
    # PAESE
    # -------------------------
    orders["Paese (Mercato)"] = orders["Paese dell'acquirente"].apply(map_country_ebay)

    # -------------------------
    # ORDER ID
    # -------------------------
    orders["Order ID (Codice Market)"] = orders["Numero ordine"]

    # -------------------------
    # PRODOTTO (SKU logic richiesta)
    # -------------------------
    def get_product(row):
        sku = row.get("Etichetta personalizzata")
        title = row.get("Titolo")

        # se SKU vuoto → titolo o codice
        if pd.notna(sku) and str(sku).strip() != "":
            return sku

        if pd.notna(title) and str(title).strip() != "":
            return title

        return ""

    orders["Prodotto"] = orders.apply(get_product, axis=1)

    # -------------------------
    # QUANTITÀ
    # -------------------------
    orders["Quantità ordinata"] = pd.to_numeric(
        orders["Quantità"],
        errors="coerce"
    ).fillna(0)

    # -------------------------
    # FATTURATO LORDO
    # -------------------------
    orders["Fatturato (Lordo)"] = orders["Costo totale"].apply(to_float)

    # -------------------------
    # FEES ORDINE (solo righe ordine)
    # -------------------------
    def safe_sum(df, cols):
        return sum(df[c].apply(to_float) if c in df.columns else 0 for c in cols)

    orders["Fee (€)"] = (
        safe_sum(orders, [
            "Commissione sul valore finale - fissa",
            "Commissione sul valore finale - variabile",
            "Tariffa per l'adeguamento normativo"
        ])
    )

    # -------------------------
    # EBAY ADS (righe separate)
    # -------------------------
    ads = ebay[ebay["Tipo di imposte riscosse e versate da eBay"].fillna("").str.contains("Tariffa Inserzioni sponsorizzate", na=False)]

    if not ads.empty:
        ads_fee = ads.copy()
        ads_fee = ads_fee.groupby("Numero ordine", as_index=False).agg({
            "Data vendita": "first",
            "Paese dell'acquirente": "first",
            "Costo totale": "sum"
        })

        ads_fee["Data ordine"] = pd.to_datetime(
            ads_fee["Data vendita"].apply(parse_ebay_date),
            errors="coerce"
        ).dt.strftime("%d/%m/%Y")

        ads_fee["Marketplace"] = "eBay"
        ads_fee["Paese (Mercato)"] = ads_fee["Paese dell'acquirente"].apply(map_country_ebay)
        ads_fee["Order ID (Codice Market)"] = ads_fee["Numero ordine"]
        ads_fee["Prodotto"] = "Tariffa Inserzioni Sponsorizzate"
        ads_fee["Quantità ordinata"] = 0
        ads_fee["Fatturato (Lordo)"] = 0
        ads_fee["Fee (€)"] = ads_fee["Costo totale"].apply(to_float)

        ads_fee = ads_fee[[
            "Data ordine",
            "Marketplace",
            "Paese (Mercato)",
            "Order ID (Codice Market)",
            "Prodotto",
            "Quantità ordinata",
            "Fatturato (Lordo)",
            "Fee (€)"
        ]]

        ebay_df = pd.concat([orders, ads_fee], ignore_index=True)
    else:
        ebay_df = orders
