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
# SAFE QUERY
# =========================
def safe_fetch(table):
    try:
        res = supabase.table(table).select("*").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Errore fetch {table}: {e}")
        return []


# =========================
# STOCK ENGINE
# =========================
def get_stock(product_id):

    try:
        res = supabase.table("stock_movements") \
            .select("type, quantity") \
            .eq("product_id", product_id) \
            .execute()

        movements = res.data or []

    except:
        return 0

    stock = 0

    for m in movements:
        t = m.get("type")
        q = m.get("quantity", 0)

        if t == "in":
            stock += q
        elif t == "out":
            stock -= q
        elif t == "return":
            stock += q

    return stock


# =========================
# MENU
# =========================
menu = st.sidebar.radio(
    "Menu",
    ["📦 Prodotti", "🛒 Ordini", "📥 Carico magazzino", "📊 Dashboard"]
)


# =========================
# 📦 PRODOTTI
# =========================
if menu == "📦 Prodotti":

    st.header("📦 Prodotti")

    # =========================
    # CREATE PRODUCT
    # =========================
    with st.form("product_form"):

        st.subheader("➕ Nuovo prodotto")

        name = st.text_input("Nome prodotto")
        sku = st.text_input("SKU (UNIVOCO)")
        supplier = st.text_input("Fornitore")
        cost = st.number_input("Costo", min_value=0.0, step=0.1)
        product_type = st.selectbox("Tipo prodotto", ["stock", "dropshipping"])
        stock_in = st.number_input("Stock iniziale", min_value=0, step=1)

        submit = st.form_submit_button("Salva")

        if submit and name and sku:

            try:
                product_res = supabase.table("products").insert({
                    "name": name,
                    "sku": sku,
                    "supplier": supplier,
                    "cost": cost,
                    "product_type": product_type
                }).execute()

                product_data = product_res.data or []

                if product_data and product_type == "stock":
                    supabase.table("stock_movements").insert({
                        "product_id": product_data[0]["id"],
                        "type": "in",
                        "quantity": stock_in,
                        "reference": "initial_stock"
                    }).execute()

                st.success("Prodotto creato!")
                st.rerun()

            except Exception as e:
                st.error(f"Errore inserimento: {e}")

    st.divider()

    # =========================
    # TABS UI
    # =========================
    tab1, tab2 = st.tabs(["📦 Magazzino", "🚚 Dropshipping"])

    products_all = safe_fetch("products")

    # =========================
    # MAGAZZINO
    # =========================
    with tab1:

        st.subheader("📦 Prodotti in magazzino")

        search = st.text_input("🔎 Cerca magazzino")

        rows = []

        for p in products_all:

            if (p.get("product_type") or "stock") != "stock":
                continue

            stock = get_stock(p.get("id"))

            if search:
                if search.lower() not in (p.get("name","").lower()) and search.lower() not in (p.get("sku","").lower()):
                    continue

            rows.append({
                "SKU": p.get("sku"),
                "Nome": p.get("name"),
                "Fornitore": p.get("supplier"),
                "Stock": stock,
                "Costo": p.get("cost")
            })

        st.dataframe(rows, use_container_width=True, height=500)

    # =========================
    # DROPSHIPPING
    # =========================
    with tab2:

        st.subheader("🚚 Catalogo Dropshipping")

        search_ds = st.text_input("🔎 Cerca dropshipping")

        rows = []

        for p in products_all:

            if p.get("product_type") != "dropshipping":
                continue

            if search_ds:
                if search_ds.lower() not in (p.get("name","").lower()) and search_ds.lower() not in (p.get("sku","").lower()):
                    continue

            rows.append({
                "SKU": p.get("sku"),
                "Nome": p.get("name"),
                "Costo": p.get("cost")
            })

        st.dataframe(rows, use_container_width=True, height=500)


# =========================
# 🛒 ORDINI
# =========================
elif menu == "🛒 Ordini":

    st.header("🛒 Ordini")

    customers = safe_fetch("customers")

    if not customers:
        st.warning("Nessun cliente")
        st.stop()

    customer_map = {c["name"]: c["id"] for c in customers}

    customer = st.selectbox("Cliente", list(customer_map.keys()))
    marketplace = st.selectbox("Marketplace", ["Amazon", "Shopify", "eBay", "Altro"])
    order_date = st.date_input("Data ordine")

    if st.button("Crea ordine"):
        try:
            supabase.table("orders").insert({
                "customer_id": customer_map[customer],
                "marketplace": marketplace,
                "order_date": str(order_date),
                "status": "pending"
            }).execute()

            st.success("Ordine creato!")
        except Exception as e:
            st.error(e)

    st.divider()

    orders = safe_fetch("orders")
    products = safe_fetch("products")

    if not orders:
        st.info("Nessun ordine")
        st.stop()

    order_map = {
        f"{o.get('id')} | {o.get('marketplace')} | {o.get('order_date')}": o.get("id")
        for o in orders
    }

    selected_order = st.selectbox("Seleziona ordine", list(order_map.keys()))
    order_id = order_map[selected_order]

    st.subheader("📦 Aggiungi prodotti")

    sku_map = {p.get("sku"): p for p in products if p.get("sku")}

    selected_sku = st.selectbox("SKU prodotto", list(sku_map.keys()))

    quantity = st.number_input("Quantità", min_value=1, value=1)
    sale_price = st.number_input("Prezzo vendita", min_value=0.0)
    returned = st.checkbox("Reso")

    if st.button("Aggiungi"):

        try:
            product = sku_map[selected_sku]
            product_id = product.get("id")

            profit = 0
            if product.get("product_type") == "dropshipping":
                profit = (sale_price - (product.get("cost") or 0)) * quantity

            supabase.table("order_items").insert({
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "sale_price": sale_price,
                "returned": returned
            }).execute()

            if product.get("product_type") == "stock":

                movement_type = "return" if returned else "out"

                supabase.table("stock_movements").insert({
                    "product_id": product_id,
                    "type": movement_type,
                    "quantity": quantity,
                    "reference": f"{movement_type}:{order_id}"
                }).execute()

            st.success(f"Aggiornato! Profitto: {profit:.2f} €")

        except Exception as e:
            st.error(e)


# =========================
# 📥 CARICO MAGAZZINO
# =========================
elif menu == "📥 Carico magazzino":

    st.header("📥 Carico magazzino")

    products = safe_fetch("products")

    sku_map = {p.get("sku"): p for p in products if p.get("sku")}

    selected_sku = st.selectbox("SKU prodotto", list(sku_map.keys()))

    quantity = st.number_input("Quantità ricevuta", min_value=1, value=1)
    note = st.text_input("Nota")

    if st.button("Registra carico"):

        try:
            product = sku_map[selected_sku]

            if product.get("product_type") == "stock":

                supabase.table("stock_movements").insert({
                    "product_id": product.get("id"),
                    "type": "in",
                    "quantity": quantity,
                    "reference": note or "replenishment"
                }).execute()

                st.success("Carico registrato!")
            else:
                st.warning("Prodotto dropshipping")

        except Exception as e:
            st.error(e)


# =========================
# 📊 DASHBOARD
# =========================
elif menu == "📊 Dashboard":

    st.header("📊 Dashboard ERP")

    products = safe_fetch("products")
    orders = safe_fetch("orders")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("📦 Prodotti", len(products))

    with col2:
        st.metric("🛒 Ordini", len(orders))
