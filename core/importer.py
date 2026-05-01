def import_to_supabase(data, supabase):

    # 1. crea ordine
    order_res = supabase.table("ordini").insert(data["orders"]).execute()

    order_id = order_res.data[0]["id"]

    # 2. collega righe
    for r in data["rows"]:
        r["ordine_id"] = order_id

    # 3. inserisci righe
    if data["rows"]:
        supabase.table("righe_ordine").insert(data["rows"]).execute()

    return order_id
