/*
  Silver: daily_prices (clean)
 
  Final, business-ready daily price table. Rows with hard data quality
  failures are excluded here and land in silver_daily_prices_quarantine
  instead. Soft-flagged rows (e.g. zero volume, missing overview match)
  ARE included here, with their flag columns intact, so downstream
  consumers can see and decide how to treat them - per Step 11,
  we flag rather than silently delete.
*/

select
    symbol,
    trade_date,
    open,
    high,
    low,
    close,
    volume,
    flag_zero_volume,
    flag_missing_company_overview
from {{ ref('int_daily_prices_flagged') }}
where not is_quarantined