"""Top gainers and losers on the most recent trading day."""

import streamlit as st
from db import run_query


def render(catalog: str, schema: str) -> None:
    st.subheader("Top movers (latest trading day)")

    data = run_query(f"""
        SELECT symbol, trade_date, daily_return_pct
        FROM {catalog}.{schema}.fact_daily_returns
        WHERE trade_date = (SELECT max(trade_date) FROM {catalog}.{schema}.fact_daily_returns)
          AND daily_return_pct IS NOT NULL
        ORDER BY daily_return_pct DESC
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top gainers**")
        st.dataframe(
            data.head(5)[["symbol", "daily_return_pct"]].rename(
                columns={"symbol": "Symbol", "daily_return_pct": "Return"}
            ),
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.markdown("**Top losers**")
        st.dataframe(
            data.tail(5).sort_values("daily_return_pct")[["symbol", "daily_return_pct"]].rename(
                columns={"symbol": "Symbol", "daily_return_pct": "Return"}
            ),
            use_container_width=True,
            hide_index=True,
        )