"""Valuation and profitability comparison across all tracked companies."""

import streamlit as st
from db import run_query


def render(catalog: str, schema: str) -> None:
    st.subheader("Valuation and profitability comparison")

    data = run_query(f"""
        SELECT symbol, trailing_pe, peg_ratio, profit_margin, return_on_equity_ttm
        FROM {catalog}.{schema}.dim_company
        ORDER BY symbol
    """)

    tab1, tab2, tab3, tab4 = st.tabs(["Trailing P/E", "PEG ratio", "Profit margin", "Return on equity"])

    with tab1:
        st.bar_chart(data.set_index("symbol")["trailing_pe"])
    with tab2:
        st.bar_chart(data.set_index("symbol")["peg_ratio"])
    with tab3:
        st.bar_chart(data.set_index("symbol")["profit_margin"])
    with tab4:
        st.bar_chart(data.set_index("symbol")["return_on_equity_ttm"])