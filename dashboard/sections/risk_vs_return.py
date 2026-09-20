"""Risk vs return scatter - answers "which sectors have the best
risk-adjusted returns", the original project's core business question."""

import streamlit as st
import pandas as pd


def render(sector_data: pd.DataFrame) -> None:
    st.subheader("Risk vs return by sector")
    st.caption("Which sectors have the best risk-adjusted returns?")

    latest_date = sector_data["trade_date"].max()
    latest = sector_data[sector_data["trade_date"] == latest_date].copy()

    # Sharpe-style ratio: higher is better (more return per unit of risk)
    latest["risk_adjusted_ratio"] = latest["avg_daily_return_pct"] / latest["avg_volatility_20d"]

    st.scatter_chart(
        latest,
        x="avg_volatility_20d",
        y="avg_daily_return_pct",
        color="sector",
        size="risk_adjusted_ratio",
    )

    st.dataframe(
        latest[["sector", "avg_daily_return_pct", "avg_volatility_20d", "risk_adjusted_ratio"]]
        .sort_values("risk_adjusted_ratio", ascending=False)
        .rename(columns={
            "avg_daily_return_pct": "Avg daily return",
            "avg_volatility_20d": "Avg volatility (20d)",
            "risk_adjusted_ratio": "Risk-adjusted ratio",
        }),
        use_container_width=True,
        hide_index=True,
    )