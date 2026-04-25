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
menu = st.sidebar.radio("Menu", ["📦 Prodotti", "📊 Dashboard"])

# =========================
# PRODOTTI
# =========================
if menu == "📦 Prodotti":

    st.header("📦 Prodotti")

    # ---- FORM INSERIMENTO ----
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

    # ---- LISTA PRODOTTI ----
    st.subheader("📋 Lista prodotti")

    data = supabase.table("products").select("*").execute().data

    if data:
        st.dataframe(data, use_container_width=True)
    else:
        st.info("Nessun prodotto trovato")

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
