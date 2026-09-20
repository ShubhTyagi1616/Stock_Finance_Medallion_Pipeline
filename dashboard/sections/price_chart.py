"""Selected ticker's close price with a 20-day moving average overlay."""

import streamlit as st
from db import run_query


def render(catalog: str, schema: str) -> None:
    st.subheader("Price chart")

    tickers = run_query(f"SELECT DISTINCT symbol FROM {catalog}.{schema}.dim_company ORDER BY symbol")
    selected = st.selectbox("Select a ticker", tickers["symbol"], key="price_chart_ticker")

    price_data = run_query(f"""
        SELECT trade_date, close, moving_avg_20d
        FROM {catalog}.{schema}.fact_daily_returns
        WHERE symbol = '{selected}'
        ORDER BY trade_date
    """)

    chart_data = price_data.set_index("trade_date")[["close", "moving_avg_20d"]]
    chart_data.columns = ["Close price", "20-day moving average"]
    st.line_chart(chart_data)