import pandas as pd

# 🔥 converte euro in modo sicuro (GESTISCE TUTTO)
def euro(x):
    try:
        if pd.isna(x):
            return 0
        return float(
            str(x)
            .replace("€", "")
            .replace(" ", "")
            .replace(",", ".")
            .strip()
        )
    except:
        return 0


def clean(v):
    if pd.isna(v):
        return None
    return str(v).strip()


def parse_temu(file):

    df = pd.read_excel(file)

    # 🔥 pulizia colonne
    df.columns = df.columns.str.strip()

    orders = {}

    for _, row in df.iterrows():

        order_id = clean(row["ID Ordine"])

        if order_id not in orders:
            orders[order_id] = {
                "order_id": order_id,
                "country": clean(row.get("Paese di spedizione")),
                "date": clean(row.get("data di acquisto")),
                "items": []
            }

        # 🔥 REVENUE CORRETTO
        revenue = (
            euro(row.get("Totale prezzo base")) +
            euro(row.get("Totale spedizione (imposte escluse)")) +
            euro(row.get("Imposta sull'articolo")) +
            euro(row.get("Imposta sulla spedizione"))
        )

        orders[order_id]["items"].append({
            "sku": clean(row.get("Codice SKU")),
            "qty": int(row.get("quantità acquistata") or 0),
            "revenue": revenue
        })

    return orders
