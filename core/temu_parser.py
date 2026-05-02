import pandas as pd

def euro(x):
    if pd.isna(x):
        return 0
    return float(str(x).replace("€","").replace(",",".").strip())

def parse_temu(file):

    df = pd.read_excel(file)

    # 🔥 FIX IMPORTANTE: pulisce colonne
    df.columns = df.columns.str.strip()

    orders = {}

    for _, row in df.iterrows():

        order_id = row["ID Ordine"]

        if order_id not in orders:
            orders[order_id] = {
                "order_id": order_id,
                "country": row.get("Paese di spedizione", ""),
                "date": row.get("data di acquisto", None),
                "items": []
            }

        revenue = (
            euro(row.get("Totale prezzo base", 0)) +
            euro(row.get("Totale spedizione (imposte escluse)", 0)) +
            euro(row.get("Imposta sull'articolo", 0)) +
            euro(row.get("Imposta sulla spedizione", 0))
        )

        orders[order_id]["items"].append({
            "sku": row.get("Codice SKU", ""),
            "qty": int(row.get("quantità acquistata", 0) or 0),
            "revenue": revenue
        })

    return orders
