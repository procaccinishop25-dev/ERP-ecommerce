def transform(df, marketplace, mercato):

    df.columns = [c.strip() for c in df.columns]

    numero_ordine = str(df["Order ID"].iloc[0])
    data_ordine = df["Order Date"].iloc[0]

    order = {
        "numero_ordine": numero_ordine,
        "data_ordine": data_ordine,
        "marketplace": marketplace,
        "mercato": mercato,
        "fatturato_totale": df["Total"].sum()
    }

    rows = []

    for _, r in df.iterrows():
        rows.append({
            "sku_prodotto": r["SKU"],
            "quantita": int(r["Quantity"]),
            "prezzo_unitario": float(r["Unit Price"]),
            "totale_riga": float(r["Total"])
        })

    return {
        "orders": [order],
        "rows": rows
    }
