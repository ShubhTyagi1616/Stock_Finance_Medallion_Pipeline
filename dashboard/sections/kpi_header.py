"""KPI header: companies tracked, latest trade date, average market cap."""

import streamlit as st
from db import run_query


def render(catalog: str, schema: str) -> None:
    kpi_data = run_query(f"""
        SELECT
            (SELECT count(DISTINCT symbol) FROM {catalog}.{schema}.dim_company) AS num_companies,
            (SELECT max(trade_date) FROM {catalog}.{schema}.fact_daily_prices) AS latest_date,
            (SELECT avg(market_cap) FROM {catalog}.{schema}.dim_company) AS avg_market_cap
    """)

    col1, col2, col3 = st.columns(3)
    col1.metric("Companies tracked", int(kpi_data["num_companies"][0]))
    col2.metric("Latest trade date", str(kpi_data["latest_date"][0]))
    col3.metric("Avg market cap", f"${kpi_data['avg_market_cap'][0] / 1e9:.1f}B")