/*
  Intermediate: daily_prices_flagged

  Explodes Bronze JSON, types columns, deduplicates, then computes
  data quality flags. This model is not queried directly by end users -
  silver_daily_prices.sql and silver_daily_prices_quarantine.sql both
  read from it and split the rows.

  Flag categories:
  - HARD failures (flag_* = true means quarantine): missing required
    fields, impossible OHLC values, future-dated records.
  - SOFT flags (kept in the clean table, just marked): zero volume,
    symbol missing from company_overview. These are worth knowing about
    but not serious enough to throw the row away.
*/

{{ config(schema='silver') }}

with exploded as (

    select
        upper(trim(b.raw_json:['Meta Data']:['2. Symbol']::string)) as symbol,
        e.key as trade_date_str,
        e.value as day_data
    from {{ source('bronze', 'raw_daily_prices') }} b,
    lateral variant_explode(b.raw_json:['Time Series (Daily)']) as e

),

typed as (

    select
        symbol,
        try_cast(trade_date_str as date) as trade_date,
        day_data:['1. open']::double as open,
        day_data:['2. high']::double as high,
        day_data:['3. low']::double as low,
        day_data:['4. close']::double as close,
        day_data:['5. volume']::bigint as volume
    from exploded

),

deduplicated as (

    select *
    from (
        select
            *,
            row_number() over (
                partition by symbol, trade_date
                order by trade_date
            ) as row_num
        from typed
    )
    where row_num = 1

),

flagged as (

    select
        d.symbol,
        d.trade_date,
        d.open,
        d.high,
        d.low,
        d.close,
        d.volume,

        -- Step 3: mandatory null checks (hard failure)
        (d.symbol is null
         or d.trade_date is null
         or d.close is null
         or d.volume is null) as flag_missing_required_field,

        -- Step 6: amount/price validation (hard failure - impossible data)
        (d.high is not null and d.low is not null and d.high < d.low) as flag_ohlc_inconsistent,
        (d.close is not null and d.close <= 0) as flag_nonpositive_price,
        (d.volume is not null and d.volume < 0) as flag_negative_volume,

        -- Step 6 (soft): zero volume is unusual but not impossible
        -- (e.g. trading halt) - flagged, not quarantined
        (d.volume is not null and d.volume = 0) as flag_zero_volume,

        -- Step 7: date validation (hard failure)
        (d.trade_date is not null and d.trade_date > current_date()) as flag_future_date,

        -- Step 8: referential integrity (soft flag, not quarantined -
        -- overview data comes from a separate ingestion path and gaps
        -- there shouldn't discard otherwise-valid price history)
        (o.symbol is null) as flag_missing_company_overview

    from deduplicated d
    left join {{ ref('silver_company_overview') }} o
        on d.symbol = o.symbol

)

select
    *,
    (flag_missing_required_field
     or flag_ohlc_inconsistent
     or flag_nonpositive_price
     or flag_negative_volume
     or flag_future_date) as is_quarantined
from flagged