/*
  Check #2: Row count reconciliation.
  fact_daily_prices does no filtering vs silver_daily_prices, only
  joining - so their row counts must match exactly. A dbt test PASSES
  when this query returns ZERO rows, so we select only if they differ.
*/

{{ config(tags=['gold']) }}

with silver_count as (
    select count(*) as cnt from {{ ref('silver_daily_prices') }}
),
gold_count as (
    select count(*) as cnt from {{ ref('fact_daily_prices') }}
)

select silver_count.cnt as silver_row_count, gold_count.cnt as gold_row_count
from silver_count, gold_count
where silver_count.cnt != gold_count.cnt