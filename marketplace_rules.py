def calcola_totale_riga(row, marketplace):

    base = row["quantita"] * row["prezzo_unitario"]

    if marketplace == "AMAZON":
        return base - 1

    if marketplace == "EBAY":
        return base - 0.5

    return base
