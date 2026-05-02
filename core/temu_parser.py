import pandas as pd
from utils.helpers import parse_euro
from core.config import TEMU_COLUMNS

def parse_temu(file):

    df = pd.read_excel(file)

    orders = {}

    for _, row in df.iterrows():

        order_id = row[TEMU_COLUMNS["order_id"]]

        if order_id not in orders:
            orders[order_id] = {
                "order_id": order_id,
                "date": row[TEMU_COLUMNS["date"]],
                "country": row[TEMU_COLUMNS["country"]],
                "items": []
            }

        product = parse_euro(row[TEMU_COLUMNS["product_revenue"]])
        shipping = parse_euro(row[TEMU_COLUMNS["shipping"]])
        tax_item = parse_euro(row[TEMU_COLUMNS["tax_item"]])
        tax_shipping = parse_euro(row[TEMU_COLUMNS["tax_shipping"]])

        revenue = product + shipping + tax_item + tax_shipping

        orders[order_id]["items"].append({
            "sku": row[TEMU_COLUMNS["sku"]],
            "name": row[TEMU_COLUMNS["name"]],
            "qty": int(row[TEMU_COLUMNS["qty"]]),
            "revenue": revenue
        })

    return orders
