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
# STOCK ENGINE
# =========================
def get_stock(product_id):

    res = supabase.table("stock_movements") \
        .select("type, quantity") \
        .eq("product_id", product_id) \
        .execute()

    movements = res.data or []

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
# MENU
# =========================
menu = st.sidebar.radio(
    "Menu",
    ["📦 Magazzino", "🚚 Dropshipping", "🛒 Ordini", "📥 Carico magazzino", "📊 Dashboard"]
)


# =========================
# 📦 MAGAZZINO (STOCK)
# =========================
if menu == "📦 Magazzino":

    st.header("📦 Magazzino")

    search = st.text_input("🔎 Cerca prodotto")

    products = supabase.table("products") \
        .select("*") \
        .eq("product_type", "stock") \
        .execute().data or []

    rows = []

    for p in products:

        stock = get_stock(p["id"])

        if search:
            if search.lower() not in (p["name"] or "").lower() and search.lower() not in (p["sku"] or "").lower():
                continue

        rows.append({
            "SKU": p["sku"],
            "Nome": p["name"],
            "Fornitore": p["supplier"],
            "Stock": stock,
            "Costo": p["cost"]
        })

    st.subheader("📦 Prodotti in magazzino")
    st.dataframe(rows, use_container_width=True, height=600)


# =========================
# 🚚 DROPSHIPPING
# =========================
elif menu == "🚚 Dropshipping":

    st.header("🚚 Dropshipping")

    search = st.text_input("🔎 Cerca prodotto dropshipping")

    products = supabase.table("products") \
        .select("*") \
        .eq("product_type", "dropshipping") \
        .execute().data or []

    rows = []

    for p in products:

        if search:
            if search.lower() not in (p["name"] or "").lower() and search.lower() not in (p["sku"] or "").lower():
                continue

        rows.append({
            "SKU": p["sku"],
            "Nome": p["name"],
            "Costo": p["cost"]
        })

    st.subheader("🚚 Catalogo dropshipping")
    st.dataframe(rows, use_container_width=True, height=600)


# =========================
# 🛒 ORDINI
# =========================
elif menu == "🛒 Ordini":

    st.header("🛒 Ordini")

    customers = supabase.table("customers").select("*").execute().data or []

    if not customers:
        st.warning("Nessun cliente")
        st.stop()

    customer_map = {c["name"]: c["id"] for c in customers}

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

    orders = supabase.table("orders").select("*").execute().data or []
    products = supabase.table("products").select("*").execute().data or []

    order_map = {
        f"{o['id']} | {o['marketplace']} | {o['order_date']}": o["id"]
        for o in orders
    }

    selected_order = st.selectbox("Seleziona ordine", list(order_map.keys()))
    order_id = order_map[selected_order]

    st.divider()

    st.subheader("📦 Aggiungi prodotti")

    sku_map = {p["sku"]: p for p in products if p.get("sku")}

    selected_sku = st.selectbox("SKU prodotto", list(sku_map.keys()))

    quantity = st.number_input("Quantità", min_value=1, value=1)
    sale_price = st.number_input("Prezzo vendita", min_value=0.0)
    returned = st.checkbox("Reso")

    if st.button("Aggiungi"):

        product = sku_map[selected_sku]
        product_id = product["id"]

        profit = (sale_price - product["cost"]) * quantity if product["product_type"] == "dropshipping" else 0

        supabase.table("order_items").insert({
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "sale_price": sale_price,
            "returned": returned
        }).execute()

        if product["product_type"] == "stock":

            supabase.table("stock_movements").insert({
                "product_id": product_id,
                "type": "return" if returned else "out",
                "quantity": quantity,
                "reference": f"order:{order_id}"
            }).execute()

        st.success(f"Aggiornato! Profitto DS: {profit:.2f} €")


# =========================
# 📥 CARICO MAGAZZINO
# =========================
elif menu == "📥 Carico magazzino":

    st.header("📥 Carico magazzino")

    products = supabase.table("products").select("*").execute().data or []

    sku_map = {p["sku"]: p for p in products if p.get("sku")}

    selected_sku = st.selectbox("SKU prodotto", list(sku_map.keys()))

    quantity = st.number_input("Quantità ricevuta", min_value=1, value=1)
    note = st.text_input("Nota")

    if st.button("Registra carico"):

        product = sku_map[selected_sku]

        if product["product_type"] == "stock":

            supabase.table("stock_movements").insert({
                "product_id": product["id"],
                "type": "in",
                "quantity": quantity,
                "reference": note or "replenishment"
            }).execute()

            st.success("Carico registrato!")
        else:
            st.warning("Questo prodotto è dropshipping")


# =========================
# 📊 DASHBOARD
# =========================
elif menu == "📊 Dashboard":

    st.header("📊 Dashboard ERP")

    products = supabase.table("products").select("*").execute().data or []
    orders = supabase.table("orders").select("*").execute().data or []

    col1, col2 = st.columns(2)

    with col1:
        st.metric("📦 Prodotti", len(products))

    with col2:
        st.metric("🛒 Ordini", len(orders))

    st.success("Sistema stabile: stock + dropshipping separati")
