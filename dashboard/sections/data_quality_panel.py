"""Data quality transparency: surfaces the flag columns and quarantine
counts built throughout Silver and Gold, rather than leaving them as
backend-only logic invisible to anyone viewing the dashboard."""

import streamlit as st
from db import run_query


def render(catalog: str, schema: str) -> None:
    st.subheader("Data quality transparency")

    silver_schema = schema.replace("gold", "silver")

    silver_flags = run_query(f"""
        SELECT
            sum(CASE WHEN flag_zero_volume THEN 1 ELSE 0 END) AS zero_volume_days,
            sum(CASE WHEN flag_missing_company_overview THEN 1 ELSE 0 END) AS missing_overview_links
        FROM {catalog}.{silver_schema}.silver_daily_prices
    """)

    gold_flags = run_query(f"""
        SELECT sum(CASE WHEN flag_extreme_daily_return THEN 1 ELSE 0 END) AS extreme_returns
        FROM {catalog}.{schema}.fact_daily_returns
    """)

    quarantine_counts = run_query(f"""
        SELECT
            (SELECT count(*) FROM {catalog}.{silver_schema}.silver_daily_prices_quarantine) AS prices_quarantined,
            (SELECT count(*) FROM {catalog}.{silver_schema}.silver_company_overview_quarantine) AS overview_quarantined
    """)

    col1, col2, col3 = st.columns(3)
    col1.metric("Extreme daily returns flagged", int(gold_flags["extreme_returns"][0]))
    col2.metric("Zero-volume days flagged", int(silver_flags["zero_volume_days"][0]))
    col3.metric("Rows quarantined (prices)", int(quarantine_counts["prices_quarantined"][0]))

    st.caption(
        "Flagged rows are kept and visible, not silently discarded. "
        "Quarantined rows failed a hard validation check and are excluded from Gold."
    )