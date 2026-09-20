/*
  Silver: company_overview (clean)

  Final, business-ready fundamentals table with the full metric set:
  valuation ratios, profitability, growth, and price-history stats.
  Hard-failure rows are excluded and land in
  silver_company_overview_quarantine instead. Soft-flagged rows are
  kept with their flag columns visible for downstream awareness.
*/

select
    symbol,
    company_name,
    cik,
    latest_quarter,
    sector,
    industry,

    market_cap,
    revenue_ttm,
    gross_profit_ttm,
    ebitda,

    eps,
    diluted_eps_ttm,
    profit_margin,
    operating_margin_ttm,
    return_on_assets_ttm,
    return_on_equity_ttm,
    quarterly_earnings_growth_yoy,
    quarterly_revenue_growth_yoy,

    trailing_pe,
    forward_pe,
    peg_ratio,
    price_to_sales_ratio_ttm,
    price_to_book_ratio,
    ev_to_revenue,
    ev_to_ebitda,
    beta,

    week_52_high,
    week_52_low,
    moving_avg_50d,
    moving_avg_200d,

    flag_unexpected_sector,
    flag_negative_pe,
    flag_extreme_profit_margin,
    flag_stale_fundamentals

from {{ ref('int_company_overview_flagged') }}
where not is_quarantined