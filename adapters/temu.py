def get_col(df, possible_names):
    """Trova colonna anche se cambia nome"""
    for name in possible_names:
        if name in df.columns:
            return df[name]
    return None


def transform(df, marketplace, mercato):

    # normalizza colonne base
    df.columns = df.columns.astype(str).str.strip()

    # =========================
    # ORDINE (HEADER)
    # =========================

    order_id_col = get_col(df, ["ID Ordine", "id_ordine", "Order ID"])
    date_col = get_col(df, ["data_ordine", "Data ordine", "Order Date"])

    if order_id_col is None:
        raise Exception("Colonna ID Ordine non trovata")

    numero_ordine = str(order_id_col.iloc[0])
    data_ordine = date_col.iloc[0] if date_col is not None else None

    # =========================
    # FATTURATO TOTALE TEMU
    # =========================

    def safe_sum(col_names):
        col = get_col(df, col_names)
        if col is None:
            return 0
        return col.fillna(0).astype(float).sum()

    fatturato_totale = (
        safe_sum(["Totale prezzo base dopo lo sconto"])
        + safe_sum(["Totale spedizione (imposte escluse)"])
        + safe_sum(["Imposta sull'articolo"])
        + safe_sum(["Imposta sulla spedizione"])
    )

    order = {
        "numero_ordine": numero_ordine,
        "data_ordine": data_ordine,
        "marketplace": marketplace,
        "mercato": mercato,
        "fatturato_totale": float(fatturato_totale)
    }

    # =========================
    # RIGHE
    # =========================

    sku_col = get_col(df, ["Codice SKU", "SKU"])
    qty_col = get_col(df, ["quantità acquistata", "quantita", "Quantity"])
    price_col = get_col(df, ["prezzo base della merce", "prezzo_unitario", "Price"])

    rows = []

    for i in range(len(df)):

        sku = sku_col.iloc[i] if sku_col is not None else None
        qty = qty_col.iloc[i] if qty_col is not None else 1
        price = price_col.iloc[i] if price_col is not None else 0

        try:
            qty = int(qty)
        except:
            qty = 1

        try:
            price = float(price)
        except:
            price = 0

        rows.append({
            "sku_prodotto": sku,
            "quantita": qty,
            "prezzo_unitario": price,
            "totale_riga": qty * price
        })

    return {
        "orders": [order],
        "rows": rows
    }
