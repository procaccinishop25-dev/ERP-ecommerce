def import_to_supabase(data, supabase):
    """
    data = {
        "orders": [...],
        "rows": [...]
    }
    """

    # 1. inserisci ordini e prendi ID
    order_response = supabase.table("ordini").insert(data["orders"]).execute()

    order_id = order_response.data[0]["id"]

    # 2. assegna order_id alle righe
    for r in data["rows"]:
        r["ordine_id"] = order_id

    # 3. inserisci righe
    supabase.table("righe_ordine").insert(data["rows"]).execute()

    return order_id
