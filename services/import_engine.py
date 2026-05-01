import pandas as pd
from core.supabase_client import supabase


# ======================
# SAFE DATE PARSER
# ======================
def parse_date(value):
    if pd.isna(value):
        return None
    try:
        return pd.to_datetime(value, errors="coerce").isoformat()
    except:
        return None


# ======================
# SAFE NUMBER
# ======================
def safe_float(value):
    if pd.isna(value):
        return None
    try:
        return float(value)
    except:
        return None


# ======================
# MAIN IMPORT
# ======================
def import_orders(df, config, marketplace, mercato):

    c = config["columns"]

    # pulizia colonne Excel
    df.columns = df.columns.str.strip()

    ordine_cache = {}

    for _, row in df.iterrows():

        # ======================
        # ORDER NUMBER
        # ======================
        order_number = str(row[c["order_id"]])

        # ======================
        # CHECK ORDINE ESISTENTE
        # ======================
        if order_number not in ordine_cache:

            order = supabase.table("ordini") \
                .select("*") \
                .eq("numero_ordine", order_number) \
                .execute()

            if len(order.data) == 0:

                new_order = supabase.table("ordini").insert({
                    "numero_ordine": order_number,
                    "data_ordine": parse_date(row[c["date"]]),
                    "marketplace": marketplace,
                    "mercato": mercato,
                    "fatturato_totale": 0
                }).execute()

                ordine_id = new_order.data[0]["id"]

            else:
                ordine_id = order.data[0]["id"]

            ordine_cache[order_number] = ordine_id

        else:
            ordine_id = ordine_cache[order_number]

        # ======================
        # SAFE VALUES
        # ======================
        qty = safe_float(row[c["qty"]])
        price = safe_float(row[c["price"]])

        if qty is None or price is None:
            continue

        totale_riga = qty * price

        # ======================
        # INSERT RIGA ORDINE
        # ======================
        supabase.table("righe_ordine").insert({
            "ordine_id": ordine_id,
            "sku_prodotto": str(row[c["sku"]]),
            "quantita": int(qty),
            "prezzo_unitario": float(price),
            "totale_riga": float(totale_riga)
        }).execute()

    # ======================
    # UPDATE ORDINI TOTALI
    # ======================
    orders = supabase.table("ordini").select("id").execute()

    for o in orders.data:

        righe = supabase.table("righe_ordine") \
            .select("totale_riga") \
            .eq("ordine_id", o["id"]) \
            .execute()

        totale = sum(r["totale_riga"] for r in righe.data)

        supabase.table("ordini") \
            .update({"fatturato_totale": totale}) \
            .eq("id", o["id"]) \
            .execute()
