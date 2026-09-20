/*
  Check #5: Date completeness (adapted for a trading calendar).
  Stocks only trade on weekdays, so gaps up to ~4 calendar days
  (a long weekend/holiday) are normal. A gap larger than that per
  symbol suggests a missed ingestion day, not a market closure.
*/

with gaps as (
    select
        symbol,
        trade_date,
        lag(trade_date) over (partition by symbol order by trade_date) as prev_trade_date
    from {{ ref('fact_daily_prices') }}
)

select symbol, prev_trade_date, trade_date,
       datediff(trade_date, prev_trade_date) as gap_days
from gaps
where datediff(trade_date,prev_trade_date) > 4