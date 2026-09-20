/*
  Check #12: Data quality monitoring.
  Appends one row per dbt run with row counts across every layer and
  quarantine counts - a lightweight observability trail. Since this is
  incremental (not full-refresh), history accumulates across runs
  instead of being overwritten - this table IS the "pipeline run log."
*/

{{ config(schema='gold', materialized='incremental') }}

select
   current_timestamp() as run_at,
    (select count(*) from {{ ref('silver_daily_prices') }}) as silver_prices_rows,
    (select count(*) from {{ ref('silver_daily_prices_quarantine') }}) as silver_prices_quarantined,
    (select count(*) from {{ ref('silver_company_overview') }}) as silver_overview_rows,
    (select count(*) from {{ ref('silver_company_overview_quarantine') }}) as silver_overview_quarantined,
    (select count(*) from {{ ref('fact_daily_prices') }}) as gold_fact_prices_rows,
    (select count(*) from {{ ref('dim_company') }}) as gold_dim_company_rows,
    (select max(trade_date) from {{ ref('fact_daily_prices') }}) as latest_trade_date
