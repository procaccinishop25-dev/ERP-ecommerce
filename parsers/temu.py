def parse(df):

    df.columns = df.columns.str.strip()

    df = df.rename(columns={
        "ID Ordine": "ordine_id",
        "Codice SKU": "sku_prodotto",
        "quantità acquistata": "quantita",
        "prezzo base della merce": "prezzo_unitario",
        "Data Ordine": "data_ordine"
    })

    return df
