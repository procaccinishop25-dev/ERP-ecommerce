import streamlit as st

st.set_page_config(page_title="ERP", layout="wide")

st.sidebar.title("ERP")

pagina = st.sidebar.radio(
    "Navigazione",
    ["Dashboard", "Ordini", "Import"]
)

if pagina == "Dashboard":
    import pages.dashboard as dashboard
    dashboard.show()

elif pagina == "Ordini":
    import pages.ordini as ordini
    ordini.show()

elif pagina == "Import":
    import pages.import_page as import_page
    import_page.show()
