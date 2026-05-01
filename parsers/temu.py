def parse(df):

    df = df.rename(columns={
        "ID Ordine": "ordine_id",
        "Codice SKU": "sku",
        "quantità acquistata": "quantita",
        "Totale prezzo base dopo lo sconto": "prezzo_base",
        "Totale spedizione": "spedizione",
        "Imposta sull'articolo": "imposta_articolo",
        "Imposta sulla spedizione": "imposta_spedizione"
    })

    return df
