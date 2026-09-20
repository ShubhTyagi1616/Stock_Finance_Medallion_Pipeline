/*
  Check #6: Data freshness.
  Most recent trade_date in Gold should be within the last 7 calendar
  days (covers weekends/holidays generously). Flags a stalled pipeline.
*/

select max(trade_date) as most_recent_date
from {{ ref('fact_daily_prices') }}
having max(trade_date) < date_sub(current_date(), 7)