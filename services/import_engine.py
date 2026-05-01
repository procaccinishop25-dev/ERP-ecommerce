import pandas as pd
from core.supabase_client import supabase


def parse_temudate(value):
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value, errors="coerce", utc=True)
    except:
        return None


def import_orders(df, config, marketplace, mercato):

    c = config["columns"]

    # pulizia colonne Excel
    df.columns = df.columns.str.strip()

    for _, row in df.iterrows():

        order_number = str(row[c["order_id"]])

        # ======================
        # CERCA ORDINE
        # ======================
        order = supabase.table("ordini") \
            .select("*") \
            .eq("numero_ordine", order_number) \
            .execute()

        # ======================
        # CREA ORDINE (temporaneo)
        # ======================
        if len(order.data) == 0:

            new_order = supabase.table("ordini").insert({
                "numero_ordine": order_number,
                "data_ordine": parse_temudate(row[c["date"]]),
                "marketplace": marketplace,
                "mercato": mercato,
                "fatturato_totale": 0  # verrà aggiornato dopo
            }).execute()

            ordine_id = new_order.data[0]["id"]

        else:
            ordine_id = order.data[0]["id"]

        # ======================
        # RIGA ORDINE
        # ======================
        qty = int(row[c["qty"]])
        price = float(row[c["price"]])

        totale_riga = qty * price

        supabase.table("righe_ordine").insert({
            "ordine_id": ordine_id,
            "sku_prodotto": str(row[c["sku"]]),
            "quantita": qty,
            "prezzo_unitario": price,
            "totale_riga": totale_riga
        }).execute()

    # ======================
    # UPDATE TOTALE ORDINE
    # ======================
    rows = supabase.table("righe_ordine") \
        .select("totale_riga") \
        .eq("ordine_id", ordine_id) \
        .execute()

    totale = sum(r["totale_riga"] for r in rows.data)

    supabase.table("ordini") \
        .update({"fatturato_totale": totale}) \
        .eq("id", ordine_id) \
        .execute()
