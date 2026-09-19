import streamlit as st
import pandas as pd
from engine import get_financial_data

st.set_page_config(page_title="Watchlist & Alert App", layout="wide")

st.title("📈 Watchlist & Financial Alerts (DCA Focused)")

# Подготвени тикери според новото барање
default_tickers = "NVDA, VUAA.L, KO, JNJ, O, META, GOOGL, MSFT, TSLA, AAPL, AMZN, JPM, AVGO, CVX"
user_input = st.text_input("Внесете тикери (одделени со запирка):", default_tickers)

tickers = [t.strip().upper() for t in user_input.split(",") if t.strip()]

if st.button("Освежи податоци") or "df_data" not in st.session_state:
    with st.spinner("Се преземаат податоци од Yahoo Finance..."):
        st.session_state.df_data = get_financial_data(tickers)

if "df_data" in st.session_state and not st.session_state.df_data.empty:
    df = st.session_state.df_data.copy()

    # Стилизирање на сигналите (бои)
    def highlight_signals(val):
        if "BUY" in str(val) or "DIP" in str(val):
            return "background-color: #2e7d32; color: white;"
        elif "SELL" in str(val) or "TP" in str(val):
            return "background-color: #c62828; color: white;"
        return ""

    # Дефинирање на десно порамнување и форматирање за сите ценовни/бројчени колони
    column_config = {
        "Price": st.column_config.NumberColumn("Price", format="%.2f"),
        "Mod Dip": st.column_config.NumberColumn("Mod Dip", format="%.2f"),
        "Strong Dip": st.column_config.NumberColumn("Strong Dip", format="%.2f"),
        "Mod TP": st.column_config.NumberColumn("Mod TP", format="%.2f"),
        "Strong TP": st.column_config.NumberColumn("Strong TP", format="%.2f"),
        "RSI (14)": st.column_config.NumberColumn("RSI (14)", format="%.2f"),
        "Target High": st.column_config.NumberColumn("Target High", format="%.2f"),
        "Target Low": st.column_config.NumberColumn("Target Low", format="%.2f"),
        "Target Mean": st.column_config.NumberColumn("Target Mean", format="%.2f")
    }

    st.dataframe(
        df.style.map(highlight_signals, subset=["RSI Signal", "Price Signal"]),
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=730
    )
else:
    st.warning("Нема пронајдено податоци за избраните тикери.")