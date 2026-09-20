/*
  Gold: fact_daily_returns
 
  Derived metrics per (symbol, trade_date): daily return %, 20-day
  moving average, 20-day rolling volatility (stddev of returns).
 
  Check #11 (historical anomaly detection): a daily return beyond +-20%
  for a large-cap stock is almost certainly a data error, not real
  market movement (barring extreme rare events) - flagged, not deleted,
  consistent with Silver's flag-don't-delete philosophy.
*/

{{ config(schema='gold') }}

with with_prev as (

    select
        symbol,
        trade_date,
        close,
        volume,
        lag(close) over (partition by symbol order by trade_date) as prev_close
    from {{ ref('fact_daily_prices') }}

),

with_returns as (

    select
        symbol,
        trade_date,
        close,
        volume,
        case
            when prev_close is not null and prev_close !=0
            then (close - prev_close) / prev_close
        end as daily_return_pct
    from with_prev

),

with_rolling as (

    select
        symbol,
        trade_date,
        close,
        volume,
        daily_return_pct,
        avg(close) over (
            partition by symbol order by trade_date
            rows between 19 preceding and current row
        ) as moving_avg_20d,
        stddev(daily_return_pct) over (
            partition by symbol order by trade_date
            rows between 19 preceding and current row
        ) as volatility_20d
    from with_returns

)

select
    *,
    -- Check #11: flag, don't delete - extreme single-day move worth a
    -- second look, not proof of bad data on its own
    (daily_return_pct is not null and abs(daily_return_pct)>0.20) as flag_extreme_daily_return
from with_rolling