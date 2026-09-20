"""Golden cross / death cross indicator: compares each company's 50-day
vs 200-day moving average, a classic technical trading signal."""

import streamlit as st
from db import run_query


def render(catalog: str, schema: str) -> None:
    st.subheader("Golden cross / death cross signals")
    st.caption("50-day moving average above 200-day = bullish signal (golden cross); below = bearish (death cross)")

    data = run_query(f"""
        SELECT symbol, company_name, moving_avg_50d, moving_avg_200d
        FROM {catalog}.{schema}.dim_company
        WHERE moving_avg_50d IS NOT NULL AND moving_avg_200d IS NOT NULL
        ORDER BY symbol
    """)

    data["signal"] = data.apply(
        lambda row: "Golden cross (bullish)" if row["moving_avg_50d"] > row["moving_avg_200d"]
        else "Death cross (bearish)",
        axis=1,
    )

    st.dataframe(
        data.rename(columns={
            "symbol": "Symbol",
            "company_name": "Company",
            "moving_avg_50d": "50-day MA",
            "moving_avg_200d": "200-day MA",
            "signal": "Signal",
        }),
        use_container_width=True,
        hide_index=True,
    )