def parse(df):

    df.columns = df.columns.str.strip()

    df = df.rename(columns={
        "ID Ordine": "ordine_id",
        "Codice SKU": "sku",
        "quantità acquistata": "quantita",

        "Totale prezzo base dopo lo sconto": "prezzo_base",
        "Totale spedizione (imposte escluse)": "spedizione",
        "Imposta sull'articolo": "imposta_articolo",
        "Imposta sulla spedizione": "imposta_spedizione"
    })

    return df
