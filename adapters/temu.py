def transform(df, marketplace, mercato):

    df.columns = [c.strip() for c in df.columns]

    # ordine (1 ordine per file o gruppo)
    numero_ordine = str(df["ID Ordine"].iloc[0])
    data_ordine = df["data_ordine"].iloc[0]

    fatturato = (
        df["Totale prezzo base dopo lo sconto"].fillna(0).sum()
        + df["Totale spedizione (imposte escluse)"].fillna(0).sum()
        + df["Imposta sull'articolo"].fillna(0).sum()
        + df["Imposta sulla spedizione"].fillna(0).sum()
    )

    order = {
        "numero_ordine": numero_ordine,
        "data_ordine": data_ordine,
        "marketplace": marketplace,
        "mercato": mercato,
        "fatturato_totale": float(fatturato)
    }

    rows = []

    for _, r in df.iterrows():
        qty = int(r["quantità acquistata"])
        price = float(r["prezzo base della merce"])

        rows.append({
            "sku_prodotto": r["Codice SKU"],
            "quantita": qty,
            "prezzo_unitario": price,
            "totale_riga": qty * price
        })

    return {
        "orders": [order],
        "rows": rows
    }
