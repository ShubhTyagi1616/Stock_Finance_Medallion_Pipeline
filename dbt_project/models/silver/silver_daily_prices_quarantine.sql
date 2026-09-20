/*
  Silver: daily_prices_quarantine
 
  Holds rows that failed a HARD data quality check (missing required
  fields, impossible OHLC values, negative volume, or future-dated
  records). Kept for investigation rather than silently discarded -
  Step 3 and Step 11 of the data quality checklist.
*/

select
    symbol,
    trade_date,
    open,
    high,
    low,
    close,
    volume,
    flag_missing_required_field,
    flag_ohlc_inconsistent,
    flag_nonpositive_price,
    flag_negative_volume,
    flag_future_date,
    current_timestamp() as quarantined_at
from {{ ref('int_daily_prices_flagged') }}
where is_quarantined