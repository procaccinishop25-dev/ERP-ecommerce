import streamlit as st
from supabase import create_client

# =========================
# SUPABASE
# =========================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =========================
# APP
# =========================
st.set_page_config(page_title="ERP Ecommerce", layout="wide")
st.title("📊 ERP Ecommerce")


# =========================
# STOCK ENGINE (UNCHANGED CORE)
# =========================
def get_stock(product_id):

    movements = supabase.table("stock_movements") \
        .select("type, quantity") \
        .eq("product_id", product_id) \
        .execute().data

    if not movements:
        return 0

    stock = 0

    for m in movements:
        if m["type"] == "in":
            stock += m["quantity"]
        elif m["type"] == "out":
            stock -= m["quantity"]
        elif m["type"] == "return":
            stock += m["quantity"]

    return stock


# =========================
# MENU (COMPLETO - NON RIMOSSO NULLA)
# =========================
menu = st.sidebar.radio(
    "Menu",
    ["📦 Prodotti", "🛒 Ordini", "📥 Carico magazzino", "📊 Dashboard"]
)


# =========================
# 📦 PRODOTTI (UI SCALABILE MIGLIORATA)
# =========================
if menu == "📦 Prodotti":

    st.header("📦 Prodotti")

    # -------------------------
    # CREATE PRODUCT (UNCHANGED LOGIC)
    # -------------------------
    with st.form("product_form"):

        st.subheader("➕ Nuovo prodotto")

        name = st.text_input("Nome prodotto")
        sku = st.text_input("SKU")
        supplier = st.text_input("Fornitore")
        cost = st.number_input("Costo", min_value=0.0, step=0.1)
        stock_in = st.number_input("Stock iniziale", min_value=0, step=1)

        submit = st.form_submit_button("Salva")

        if submit and name:

            product = supabase.table("products").insert({
                "name": name,
                "sku": sku,
                "supplier": supplier,
                "cost": cost
            }).execute().data[0]

            supabase.table("stock_movements").insert({
                "product_id": product["id"],
                "type": "in",
                "quantity": stock_in,
                "reference": "initial_stock"
            }).execute()

            st.success("Prodotto creato!")
            st.rerun()

    st.divider()

    # -------------------------
    # SCALABLE TABLE VIEW (NO LOSS)
    # -------------------------
    search = st.text_input("🔎 Cerca prodotto")
    stock_filter = st.selectbox("Filtro stock", ["Tutti", "OK", "LOW", "OUT"])

    products = supabase.table("products").select("*").execute().data

    rows = []

    for p in products:

        stock = get_stock(p["id"])

        if stock <= 0:
            status = "OUT"
        elif stock < 5:
            status = "LOW"
        else:
            status = "OK"

        if search:
            if search.lower() not in p["name"].lower() and search.lower() not in (p["sku"] or "").lower():
                continue

        if stock_filter != "Tutti" and status != stock_filter:
            continue

        rows.append({
            "Nome": p["name"],
            "SKU": p["sku"],
            "Fornitore": p["supplier"],
            "Stock": stock,
            "Stato": status,
            "Costo": p["cost"]
        })

    st.subheader(f"📋 Inventario ({len(rows)})")

    st.dataframe(rows, use_container_width=True, height=600)


# =========================
# 🛒 ORDINI (COMPLETO + RESI + STOCK CORRETTO)
# =========================
elif menu == "🛒 Ordini":

    st.header("🛒 Ordini")

    customers = supabase.table("customers").select("*").execute().data

    if not customers:
        st.warning("Nessun cliente")
        st.stop()

    customer_map = {c["name"]: c["id"] for c in customers}

    st.subheader("➕ Nuovo ordine")

    customer = st.selectbox("Cliente", list(customer_map.keys()))
    marketplace = st.selectbox("Marketplace", ["Amazon", "Shopify", "eBay", "Altro"])
    order_date = st.date_input("Data ordine")

    if st.button("Crea ordine"):

        supabase.table("orders").insert({
            "customer_id": customer_map[customer],
            "marketplace": marketplace,
            "order_date": str(order_date),
            "status": "pending"
        }).execute()

        st.success("Ordine creato!")

    st.divider()

    orders = supabase.table("orders").select("*").execute().data
    products = supabase.table("products").select("*").execute().data

    order_map = {
        f"{o['id']} | {o['marketplace']} | {o['order_date']}": o["id"]
        for o in orders
    }

    selected_order = st.selectbox("Seleziona ordine", list(order_map.keys()))
    order_id = order_map[selected_order]

    st.divider()

    st.subheader("📦 Aggiungi prodotti")

    product_map = {p["name"]: p["id"] for p in products}

    col1, col2, col3 = st.columns(3)

    with col1:
        product_name = st.selectbox("Prodotto", list(product_map.keys()))

    with col2:
        quantity = st.number_input("Quantità", min_value=1, value=1)

    with col3:
        sale_price = st.number_input("Prezzo vendita", min_value=0.0)

    returned = st.checkbox("Reso")

    if st.button("Aggiungi"):

        product_id = product_map[product_name]

        supabase.table("order_items").insert({
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "sale_price": sale_price,
            "returned": returned
        }).execute()

        # STOCK LOGIC (CORRETTO)
        if returned:
            supabase.table("stock_movements").insert({
                "product_id": product_id,
                "type": "return",
                "quantity": quantity,
                "reference": f"return:{order_id}"
            }).execute()
        else:
            supabase.table("stock_movements").insert({
                "product_id": product_id,
                "type": "out",
                "quantity": quantity,
                "reference": f"order:{order_id}"
            }).execute()

        st.success("Aggiornato!")

    st.divider()

    st.subheader("📊 Dettaglio ordine")

    items = supabase.table("order_items") \
        .select("*") \
        .eq("order_id", order_id) \
        .execute().data

    total = 0

    for i in items:

        subtotal = i["quantity"] * i["sale_price"]
        total += subtotal

        st.write(
            f"📦 {i['product_id']} | "
            f"Qta: {i['quantity']} | "
            f"€{i['sale_price']} | "
            f"Tot: {subtotal} | "
            f"Reso: {i['returned']}"
        )

    st.success(f"💰 Totale: {total} €")


# =========================
# 📥 CARICO MAGAZZINO (AGGIUNTO SENZA ROMPERE NULLA)
# =========================
elif menu == "📥 Carico magazzino":

    st.header("📥 Carico magazzino")

    products = supabase.table("products").select("*").execute().data
    product_map = {p["name"]: p["id"] for p in products}

    product_name = st.selectbox("Prodotto", list(product_map.keys()))
    quantity = st.number_input("Quantità ricevuta", min_value=1, value=1)
    note = st.text_input("Nota (es: fornitore / ordine)")

    if st.button("Registra carico"):

        supabase.table("stock_movements").insert({
            "product_id": product_map[product_name],
            "type": "in",
            "quantity": quantity,
            "reference": note or "replenishment"
        }).execute()

        st.success("Carico registrato!")


# =========================
# 📊 DASHBOARD (BASE STABILE)
# =========================
elif menu == "📊 Dashboard":

    st.header("📊 Dashboard ERP")

    products = supabase.table("products").select("*").execute().data
    orders = supabase.table("orders").select("*").execute().data

    col1, col2 = st.columns(2)

    with col1:
        st.metric("📦 Prodotti", len(products))

    with col2:
        st.metric("🛒 Ordini", len(orders))

    st.write("Sistema stabile → pronto per KPI e profitto reale")
