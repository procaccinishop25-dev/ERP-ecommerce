import pandas as pd

def euro(x):
    if pd.isna(x):
        return 0
    return float(str(x).replace("€","").replace(",",".").strip())

def parse_temu(file):

    df = pd.read_excel(file)

    orders = {}

    for _, row in df.iterrows():

        order_id = row["ID Ordine"]

        if order_id not in orders:
            orders[order_id] = {
                "order_id": order_id,
                "country": row["Paese di spedizione"],
                "date": row["data di acquisto"],
                "items": []
            }

        revenue = (
            euro(row["Totale prezzo base"]) +
            euro(row["Totale spedizione (imposte escluse)"]) +
            euro(row["Imposta sull'articolo"]) +
            euro(row["Imposta sulla spedizione"])
        )

        orders[order_id]["items"].append({
            "sku": row["Codice SKU"],
            "qty": int(row["quantità acquistata"]),
            "revenue": revenue
        })

    return orders
