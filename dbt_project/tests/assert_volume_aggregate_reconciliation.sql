/*
  Check #1: Aggregate reconciliation.
  Total volume in agg_sector_rollup must equal total volume in
  fact_daily_prices. Allows a tiny float tolerance for rounding.
*/

with fact_total as (
    select sum(volume) as total from {{ ref('fact_daily_prices') }}
),
gold_total as (
    select sum(total_volume) as total from {{ ref('agg_sector_rollup') }}
)

select fact_total.total as fact_total_volume, gold_total.total as rollup_total_volume
from fact_total, gold_total
where abs(fact_total.total - gold_total.total) > 1