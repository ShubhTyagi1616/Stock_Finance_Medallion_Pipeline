"""
Finance medallion pipeline dashboard - orchestrator.

Reads exclusively from Gold-layer tables (and Silver quarantine tables
for the data quality panel), consistent with the medallion architecture's
principle that Gold is what downstream consumers should read from.

Each section's actual logic lives in sections/ as its own module -
this file just sequences them, keeping the page readable end to end.
"""

import streamlit as st

from sections import (
    kpi_header,
    sector_performance,
    risk_vs_return,
    company_explorer,
    price_chart,
    cumulative_returns,
    golden_cross,
    top_movers,
    valuation_comparison,
    data_quality_panel,
    pipeline_health,
)

CATALOG = "finance_medallion_pipeline"
GOLD_SCHEMA = "silver_gold"

st.set_page_config(
    page_title="Stock Market Medallion Pipeline",
    page_icon=":material/finance:",
    layout="wide",
)

st.title("Stock Market Medallion Pipeline")
st.caption("Bronze -> Silver -> Gold, built on Databricks + Delta Lake, orchestrated with Airflow")

kpi_header.render(CATALOG, GOLD_SCHEMA)
st.divider()

sector_data = sector_performance.render(CATALOG, GOLD_SCHEMA)
st.divider()

risk_vs_return.render(sector_data)
st.divider()

company_explorer.render(CATALOG, GOLD_SCHEMA)
st.divider()

price_chart.render(CATALOG, GOLD_SCHEMA)
st.divider()

cumulative_returns.render(CATALOG, GOLD_SCHEMA)
st.divider()

golden_cross.render(CATALOG, GOLD_SCHEMA)
st.divider()

top_movers.render(CATALOG, GOLD_SCHEMA)
st.divider()

valuation_comparison.render(CATALOG, GOLD_SCHEMA)
st.divider()

data_quality_panel.render(CATALOG, GOLD_SCHEMA)
st.divider()

pipeline_health.render(CATALOG, GOLD_SCHEMA)