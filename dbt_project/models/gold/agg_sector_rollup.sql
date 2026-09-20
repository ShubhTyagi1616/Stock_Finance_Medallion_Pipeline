/*
  Gold: agg_sector_rollup
 
  Sector-level daily rollup - answers the original business question:
  "which sectors had the best risk-adjusted returns."
 
  Check #1 (aggregate reconciliation): sum of volume here should equal
  sum of volume in fact_daily_prices for the same dates - verified by
  a singular test, since this model aggregates rather than filters.
*/

{{ config(schema='gold') }}

select
    c.sector,
    p.trade_date,
    count(distinct p.symbol) as num_companies,
    avg(r.daily_return_pct) as avg_daily_return_pct,
    avg(r.volatility_20d) as avg_volatility_20d,
    sum(p.volume) as total_volume
from {{ ref('fact_daily_prices')}} p
join {{ ref('dim_company')}} c
    on p.symbol = c.symbol
left join {{ ref('fact_daily_returns')}} r
    on p.symbol = r.symbol and p.trade_date = r.trade_date
group by c.sector, p.trade_date