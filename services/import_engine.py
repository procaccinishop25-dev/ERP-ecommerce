import pandas as pd
from core.supabase_client import supabase

def import_orders(df, config, marketplace, mercato):

    c = config["columns"]

    for _, row in df.iterrows():

        order_number = str(row[c["order_id"]])

        # 1. cerca ordine
        order = supabase.table("ordini") \
            .select("*") \
            .eq("numero_ordine", order_number) \
            .execute()

        # 2. crea ordine se non esiste
        if len(order.data) == 0:

            new_order = supabase.table("ordini").insert({
                "numero_ordine": order_number,
                "data_ordine": row[c["date"]],
                "marketplace": marketplace,
                "mercato": mercato,
                "fatturato_totale": row[c["total"]]
            }).execute()

            order_id = new_order.data[0]["id"]

        else:
            order_id = order.data[0]["id"]

        qty = int(row[c["qty"]])
        price = float(row[c["price"]])

        # 3. righe ordine
        supabase.table("righe_ordine").insert({
            "ordine_id": order_id,
            "sku_prodotto": row[c["sku"]],
            "prodotto": "",
            "quantita": qty,
            "prezzo_unitario": price,
            "totale_riga": qty * price
        }).execute()
