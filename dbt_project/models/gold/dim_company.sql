/*
  Gold: dim_company
 
  Star schema dimension. One row per symbol - grain enforced by
  schema.yml's unique test (Check #3: PK/grain uniqueness).
  Business-critical columns (symbol, sector) enforced not_null
  (Check #4: null check).
 
  Widened to carry the full fundamentals set from Silver, needed for
  the dashboard's valuation/profitability panels, technical indicators
  (50/200-day moving averages for golden/death cross), and the data
  quality transparency panel (flag columns surfaced, not hidden).
*/

{{ config(schema='gold') }}

select
    symbol,
    company_name,
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

    -- surfaced for the dashboard's data quality transparency panel,
    -- rather than left buried in the quarantine-only view
    flag_unexpected_sector,
    flag_negative_pe,
    flag_extreme_profit_margin,
    flag_stale_fundamentals
 
from {{ ref('silver_company_overview') }}