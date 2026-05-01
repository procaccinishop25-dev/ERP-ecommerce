import pandas as pd
from core.supabase_client import supabase


# =========================
# PULIZIA DATA (TEMU SAFE)
# =========================
def parse_temudate(value):
    if pd.isna(value):
        return None

    try:
        return pd.to_datetime(value, errors="coerce", utc=True)
    except:
        return None


# =========================
# IMPORT ENGINE
# =========================
def import_orders(df, config, marketplace, mercato):

    c = config["columns"]

    # pulizia colonne Excel
    df.columns = df.columns.str.strip()

    for _, row in df.iterrows():

        order_number = str(row[c["order_id"]])

        # =====================
        # CERCA ORDINE
        # =====================
        order = supabase.table("ordini") \
            .select("*") \
            .eq("numero_ordine", order_number) \
            .execute()

        # =====================
        # CREA ORDINE
        # =====================
        if len(order.data) == 0:

            new_order = supabase.table("ordini").insert({
                "numero_ordine": order_number,
                "data_ordine": parse_temudate(row[c["date"]]),
                "marketplace": marketplace,
                "mercato": mercato,
                "fatturato_totale": float(row[c["total"]])
            }).execute()

            ordine_id = new_order.data[0]["id"]

        else:
            ordine_id = order.data[0]["id"]

        # =====================
        # RIGA ORDINE
        # =====================
        qty = int(row[c["qty"]]) if not pd.isna(row[c["qty"]]) else 0
        price = float(row[c["price"]]) if not pd.isna(row[c["price"]]) else 0

        supabase.table("righe_ordine").insert({
            "ordine_id": ordine_id,
            "sku_prodotto": str(row[c["sku"]]),
            "quantita": qty,
            "prezzo_unitario": price,
            "totale_riga": qty * price
        }).execute()
