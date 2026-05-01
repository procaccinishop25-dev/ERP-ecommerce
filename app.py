import streamlit as st

st.set_page_config(page_title="ERP", layout="wide")

st.sidebar.title("ERP")

pagina = st.sidebar.radio(
    "Navigazione",
    ["Dashboard", "Ordini", "Import"]
)

if pagina == "Dashboard":
    import pages.dashboard as p
    p.show()

elif pagina == "Ordini":
    import pages.ordini as p
    p.show()

elif pagina == "Import":
    import pages.import_page as p
    p.show()
