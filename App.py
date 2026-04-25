import streamlit as st
from supabase import create_client

# =========================
# SUPABASE CONNECTION
# =========================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =========================
# APP CONFIG
# =========================
st.set_page_config(page_title="ERP Ecommerce", layout="wide")

st.title("📊 ERP Ecommerce")

# =========================
# MENU
# =========================
menu = st.sidebar.radio("Menu", ["📦 Prodotti", "🛒 Ordini", "📊 Dashboard"])

# =========================
# PRODOTTI
# =========================
if menu == "📦 Prodotti":

    st.header("📦 Prodotti")

    with st.form("form_product"):
        st.subheader("➕ Aggiungi prodotto")

        name = st.text_input("Nome prodotto")
        sku = st.text_input("SKU")
        supplier = st.text_input("Fornitore")
        cost = st.number_input("Costo", min_value=0.0, step=0.1)

        submit = st.form_submit_button("Salva")

        if submit:
            if name:
                supabase.table("products").insert({
                    "name": name,
                    "sku": sku,
                    "supplier": supplier,
                    "cost": cost
                }).execute()

                st.success("Prodotto inserito!")
                st.rerun()
            else:
                st.error("Inserisci il nome prodotto")

    st.divider()

    st.subheader("📋 Lista prodotti")

    data = supabase.table("products").select("*").execute().data

    if data:
        st.dataframe(data, use_container_width=True)
    else:
        st.info("Nessun prodotto trovato")


# =========================
# ORDINI (NUOVO MODULO)
# =========================
elif menu == "🛒 Ordini":

    st.header("🛒 Ordini ERP")

    # -------------------------
    # CREA ORDINE
    # -------------------------
    st.subheader("➕ Crea ordine")

    customer_name = st.text_input("Cliente")
    marketplace = st.selectbox("Marketplace", ["Amazon", "Shopify", "eBay", "Altro"])
    order_date = st.date_input("Data ordine")

    if st.button("Crea ordine"):

        if customer_name:
            supabase.table("orders").insert({
                "customer_name": customer_name,
                "marketplace": marketplace,
                "order_date": str(order_date),
                "status": "pending"
            }).execute()

            st.success("Ordine creato!")
        else:
            st.error("Inserisci cliente")

    st.divider()

    # -------------------------
    # SELEZIONA ORDINE
    # -------------------------
    st.subheader("📌 Ordine attivo")

    orders = supabase.table("orders").select("*").execute().data

    if orders:

        order_map = {
            f"{o['customer_name']} - {o['marketplace']} - {o['order_date']}": o["id"]
            for o in orders
        }

        selected = st.selectbox("Seleziona ordine", list(order_map.keys()))
        order_id = order_map[selected]

        st.divider()

        # -------------------------
        # AGGIUNGI PRODOTTI
        # -------------------------
        st.subheader("📦 Aggiungi prodotti all'ordine")

        products = supabase.table("products").select("*").execute().data

        if products:

            product_map = {p["name"]: p["id"] for p in products}

            col1, col2, col3 = st.columns(3)

            with col1:
                product_name = st.selectbox("Prodotto", list(product_map.keys()))

            with col2:
                quantity = st.number_input("Quantità", min_value=1, value=1)

            with col3:
                sale_price = st.number_input("Prezzo vendita", min_value=0.0)

            returned = st.checkbox("Reso")

            if st.button("Aggiungi al ordine"):

                supabase.table("order_items").insert({
                    "order_id": order_id,
                    "product_id": product_map[product_name],
                    "quantity": quantity,
                    "sale_price": sale_price,
                    "returned": returned
                }).execute()

                st.success("Prodotto aggiunto!")

        st.divider()

        # -------------------------
        # DETTAGLIO ORDINE
        # -------------------------
        st.subheader("📋 Dettaglio ordine")

        items = supabase.table("order_items") \
            .select("*") \
            .eq("order_id", order_id) \
            .execute().data

        if items:

            total = 0

            for i in items:
                subtotal = i["quantity"] * i["sale_price"]
                total += subtotal

                st.write(
                    f"📦 Prodotto ID: {i['product_id']} | "
                    f"Qta: {i['quantity']} | "
                    f"Prezzo: {i['sale_price']} € | "
                    f"Tot: {subtotal} € | "
                    f"Reso: {i['returned']}"
                )

            st.success(f"💰 Totale ordine: {total} €")

        else:
            st.info("Nessun prodotto nell'ordine")

    else:
        st.info("Nessun ordine presente")


# =========================
# DASHBOARD
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

    st.write("Qui costruiremo KPI (fatturato, margini, ecc.)")
