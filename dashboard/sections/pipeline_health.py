"""Pipeline health panel: row counts and freshness from the audit log
built by the Gold layer - makes the pipeline's own observability
visible on the dashboard, not just buried in Airflow logs."""

import streamlit as st
from db import run_query


def render(catalog: str, schema: str) -> None:
    st.subheader("Pipeline health")

    audit_log = run_query(f"""
        SELECT *
        FROM {catalog}.{schema}.gold_pipeline_audit_log
        ORDER BY run_at DESC
        LIMIT 10
    """)

    if audit_log.empty:
        st.info("No pipeline runs logged yet.")
        return

    latest = audit_log.iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Last run", str(latest["run_at"]))
    col2.metric("Gold fact rows", int(latest["gold_fact_prices_rows"]))
    col3.metric("Latest trade date in Gold", str(latest["latest_trade_date"]))

    st.markdown("**Recent pipeline runs**")
    st.dataframe(audit_log, use_container_width=True, hide_index=True)