"""Sector performance: avg daily return and volatility over time, per sector."""

import streamlit as st
from db import run_query


def render(catalog: str, schema: str) -> None:
    st.subheader("Sector performance over time")

    sector_data = run_query(f"""
        SELECT sector, trade_date, avg_daily_return_pct, avg_volatility_20d
        FROM {catalog}.{schema}.agg_sector_rollup
        ORDER BY trade_date
    """)

    tab1, tab2 = st.tabs(["Average daily return", "Average volatility"])

    with tab1:
        pivot_return = sector_data.pivot(index="trade_date", columns="sector", values="avg_daily_return_pct")
        st.line_chart(pivot_return)

    with tab2:
        pivot_vol = sector_data.pivot(index="trade_date", columns="sector", values="avg_volatility_20d")
        st.line_chart(pivot_vol)

    return sector_data  # reused by risk_vs_return to avoid a duplicate query