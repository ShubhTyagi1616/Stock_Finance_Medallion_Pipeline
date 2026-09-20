"""Cumulative return chart: growth of $1 invested per ticker since data
start - a classic portfolio-style visual, computed from daily returns."""

import streamlit as st  
from db import run_query


def render(catalog: str, schema: str) -> None:
    st.subheader("Cumulative return since tracking began")
    st.caption("Growth of $1 invested on the first tracked day, per ticker")

    returns_data = run_query(f"""
        SELECT symbol, trade_date, daily_return_pct
        FROM {catalog}.{schema}.fact_daily_returns
        WHERE daily_return_pct IS NOT NULL
        ORDER BY symbol, trade_date
    """)

    #compound daily return per symbol: cumulative product of (1 + return)

    returns_data["growth_factor"] = 1 + returns_data["daily_return_pct"]
    returns_data["cumulative_value"] = (
        returns_data.groupby("symbol")["growth_factor"].cumprod()
    )

    pivot = returns_data.pivot(index="trade_date", columns="symbol", values="cumulative_value")
    st.line_chart(pivot)