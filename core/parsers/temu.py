import pandas as pd

def parse(file):

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
        orders[order_id]["items"].append({
            "sku": row["Codice SKU"],
            "qty": int(row["quantità acquistata"]),
            "revenue": 0
        })

    return orders
