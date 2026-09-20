"""Filterable company table: sector, P/E, beta, 52-week range."""

import streamlit as st  
from db import run_query


def render(catalog: str, schema: str) -> None:
    st.subheader("Company explorer")

    company_data = run_query(f"""
        SELECT symbol, company_name, sector, market_cap, trailing_pe, forward_pe,
                beta, week_52_high, week_52_low
        FROM {catalog}.{schema}.dim_company
        ORDER BY symbol 
        """)

    sector_filter = st.multiselect(
        "Filter by sector",
        options=sorted(company_data["sector"].dropna().unique()),
        default=None,
        key="company_explorer_sector_filter",
    )

    filtered = company_data if not sector_filter else company_data[company_data["sector"].isin(sector_filter)]

    st.dataframe(
        filtered.rename(columns={
            "symbol": "Symbol",
            "company_name": "Company",
            "sector": "Sector",
            "market_cap": "Market cap",
            "trailing_pe": "Trailing P/E",
            "forward_pe": "Forward P/E",
            "beta": "Beta",
            "week_52_high": "52w High",
            "week_52_low": "52w Low",
        }),
        use_container_width=True,
        hide_index=True,
    )