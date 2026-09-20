/*
  Gold: fact_daily_prices
 
  Grain: one row per (symbol, trade_date) - enforced by schema.yml
  (Check #3: PK/grain uniqueness).
 
  Joins to dim_company using a LEFT JOIN on a table we already know is
  unique per symbol (Check #7: duplicate metric prevention - an
  accidentally many-to-one join here would silently inflate row counts,
  so dim_company's own uniqueness test is what protects this join).
 
  Row count here should equal silver_daily_prices' row count exactly -
  verified by a singular test (Check #2: transaction/row count
  reconciliation) since this model does no filtering, only joining.
*/

{{ config(schema='gold') }}

select
    p.symbol,
    p.trade_date,
    p.open,
    p.high,
    p.low,
    p.close,
    p.volume,
    c.sector,

     -- Check #9 (re-verified defense-in-depth, already filtered upstream
    -- in Silver via currency validation - this just confirms nothing
    -- slipped through)
    (p.high < p.low) as flag_ohlc_inconsistent_gold_check

from {{ ref('silver_daily_prices') }} p
left join {{ ref('dim_company') }} c
    on p.symbol = c.symbol