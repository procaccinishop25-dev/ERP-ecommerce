import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client

# =========================
# 🔐 SUPABASE (SECRETS)
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("📊 ERP Ecommerce - CONTROL CENTER")

# =========================
# ⏱ LEAD TIME
# =========================
LEAD_TIME = 10  # giorni di consegna

# =========================
# 📦 VENDITE
# =========================
st.subheader("📦 Vendite")

vendite = supabase.table("Vendite").select("*").execute()

if vendite.data:
    df_vendite = pd.DataFrame(vendite.data)

    st.metric("Totale vendite", len(df_vendite))

    if "revenue" in df_vendite.columns:
        st.metric("Fatturato totale", df_vendite["revenue"].sum())

    st.dataframe(df_vendite)
else:
    st.warning("Nessuna vendita trovata")

# =========================
# 📦 PRODOTTI
# =========================
st.subheader("📦 Anagrafica prodotti")

prodotti = supabase.table("Anagrafica prodotti").select("*").execute()

if prodotti.data:
    df_prodotti = pd.DataFrame(prodotti.data)

    st.metric("Totale prodotti", len(df_prodotti))

    st.dataframe(df_prodotti)
else:
    st.warning("Nessun prodotto trovato")

# =========================
# 📦 MOVIMENTO MAGAZZINO
# =========================
st.subheader("📦 Movimento magazzino")

magazzino = supabase.table("Movimento magazzino").select("*").execute()

if magazzino.data:
    df = pd.DataFrame(magazzino.data)

    df["date"] = pd.to_datetime(df["date"])

    # =========================
    # 📊 STOCK
    # =========================
    stock_df = df.groupby("product_sku").apply(
        lambda x: 
        x[x["type"]=="IN"]["quantity"].sum()
        - x[x["type"]=="OUT"]["quantity"].sum()
        + x[x["type"]=="RETURN"]["quantity"].sum()
        - x[x["type"]=="LOSS"]["quantity"].sum()
    ).reset_index(name="stock")

    # =========================
    # 📊 VENDITE MEDIE (7 giorni)
    # =========================
    last_7 = df[df["date"] >= (df["date"].max() - pd.Timedelta(days=7))]

    sales = last_7[last_7["type"] == "OUT"].groupby("product_sku")["quantity"].sum() / 7
    sales = sales.reset_index(name="daily_sales")

    stock_df = stock_df.merge(sales, on="product_sku", how="left")
    stock_df["daily_sales"] = stock_df["daily_sales"].fillna(0)

    # =========================
    # ⏱ COPERTURA STOCK
    # =========================
    stock_df["coverage_days"] = stock_df.apply(
        lambda x: x["stock"] / x["daily_sales"] if x["daily_sales"] > 0 else 999,
        axis=1
    )

    # =========================
    # 📦 RIORDINO QUANTITÀ
    # =========================
    TARGET_DAYS = 10

    stock_df["reorder_qty"] = stock_df.apply(
        lambda x: max(int(x["daily_sales"] * TARGET_DAYS - x["stock"]), 0),
        axis=1
    )

    # =========================
    # 🚦 SEMAFORO
    # =========================
    def status(stock):
        if stock <= 0:
            return "🔴 STOCK OUT"
        elif stock < 5:
            return "🟠 BASSO"
        elif stock < 10:
            return "🟡 ATTENZIONE"
        else:
            return "🟢 OK"

    stock_df["status"] = stock_df["stock"].apply(status)

    # =========================
    # ⚠️ DECISION ENGINE
    # =========================
    def decision(row):
        if row["stock"] <= 0:
            return "🔴 ORDINA SUBITO"
        elif row["stock"] < 5:
            return "🟠 RIORDINA PRESTO"
        elif row["stock"] < 10:
            return "🟡 MONITORA"
        else:
            return "🟢 OK"

    stock_df["azione"] = stock_df.apply(decision, axis=1)

    # =========================
    # 🚨 AUTOPILOT (CON LEAD TIME)
    # =========================
    def autopilot(row):
        if row["coverage_days"] <= LEAD_TIME:
            return "🔥 ORDINE URGENTE (rischio stock out)"
        elif row["coverage_days"] <= LEAD_TIME + 5:
            return "⚠️ ORDINA SUBITO"
        elif row["reorder_qty"] > 0:
            return "📦 PREPARA ORDINE"
        else:
            return "🟢 OK"

    stock_df["autopilot"] = stock_df.apply(autopilot, axis=1)

    # =========================
    # 📊 OUTPUT FINALE
    # =========================
    st.subheader("🧠 CONTROLLO STOCK & AUTOPILOT")

    st.dataframe(stock_df[[
        "product_sku",
        "stock",
        "daily_sales",
        "coverage_days",
        "reorder_qty",
        "status",
        "azione",
        "autopilot"
    ]])

    # =========================
    # 📋 MOVIMENTI
    # =========================
    st.subheader("📋 Storico movimenti")
    st.dataframe(df)

else:
    st.warning("Nessun movimento magazzino trovato")
