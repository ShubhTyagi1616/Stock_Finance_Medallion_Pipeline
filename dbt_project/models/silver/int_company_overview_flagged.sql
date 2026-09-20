/*
  Intermediate: company_overview_flagged

  Extracts the full set of fundamentals fields from raw VARIANT JSON,
  handling a real-world Alpha Vantage quirk: missing values often come
  back as the literal string "None" rather than a true JSON null. Every
  numeric/date field is routed through clean_numeric() / clean_date()
  helper expressions to normalize "None" -> actual NULL before casting
  (Step 2: Standardization).

  One row per symbol. Flags computed for data quality (Steps 3, 6, 7, 10).
*/

with typed as (

    select
        upper(trim(raw_json:Symbol::string)) as symbol,
        raw_json:Name::string as company_name,
        nullif(raw_json:CIK::string, 'None') as cik,
        try_cast(nullif(raw_json:LatestQuarter::string, 'None') as date) as latest_quarter,
        upper(trim(nullif(raw_json:Currency::string, 'None'))) as currency,
        upper(trim(raw_json:Sector::string)) as sector,
        raw_json:Industry::string as industry,

        try_cast(nullif(raw_json:MarketCapitalization::string, 'None') as bigint) as market_cap,
        try_cast(nullif(raw_json:RevenueTTM::string, 'None') as bigint) as revenue_ttm,
        try_cast(nullif(raw_json:GrossProfitTTM::string, 'None') as bigint) as gross_profit_ttm,
        try_cast(nullif(raw_json:EBITDA::string, 'None') as bigint) as ebitda,

        try_cast(nullif(raw_json:EPS::string, 'None') as double) as eps,
        try_cast(nullif(raw_json:DilutedEPSTTM::string, 'None') as double) as diluted_eps_ttm,
        try_cast(nullif(raw_json:ProfitMargin::string, 'None') as double) as profit_margin,
        try_cast(nullif(raw_json:OperatingMarginTTM::string, 'None') as double) as operating_margin_ttm,
        try_cast(nullif(raw_json:ReturnOnAssetsTTM::string, 'None') as double) as return_on_assets_ttm,
        try_cast(nullif(raw_json:ReturnOnEquityTTM::string, 'None') as double) as return_on_equity_ttm,
        try_cast(nullif(raw_json:QuarterlyEarningsGrowthYOY::string, 'None') as double) as quarterly_earnings_growth_yoy,
        try_cast(nullif(raw_json:QuarterlyRevenueGrowthYOY::string, 'None') as double) as quarterly_revenue_growth_yoy,

        try_cast(nullif(raw_json:TrailingPE::string, 'None') as double) as trailing_pe,
        try_cast(nullif(raw_json:ForwardPE::string, 'None') as double) as forward_pe,
        try_cast(nullif(raw_json:PEGRatio::string, 'None') as double) as peg_ratio,
        try_cast(nullif(raw_json:PriceToSalesRatioTTM::string, 'None') as double) as price_to_sales_ratio_ttm,
        try_cast(nullif(raw_json:PriceToBookRatio::string, 'None') as double) as price_to_book_ratio,
        try_cast(nullif(raw_json:EVToRevenue::string, 'None') as double) as ev_to_revenue,
        try_cast(nullif(raw_json:EVToEBITDA::string, 'None') as double) as ev_to_ebitda,
        try_cast(nullif(raw_json:Beta::string, 'None') as double) as beta,

        try_cast(nullif(raw_json:`52WeekHigh`::string, 'None') as double) as week_52_high,
        try_cast(nullif(raw_json:`52WeekLow`::string, 'None') as double) as week_52_low,
        try_cast(nullif(raw_json:`50DayMovingAverage`::string, 'None') as double) as moving_avg_50d,
        try_cast(nullif(raw_json:`200DayMovingAverage`::string, 'None') as double) as moving_avg_200d

    from {{ source('bronze', 'raw_company_overview') }}

),

deduplicated as (

    select *
    from (
        select
            *,
            row_number() over (
                partition by symbol
                order by symbol
            ) as row_num
        from typed
    )
    where row_num = 1

),

flagged as (

    select
        *,

        -- Step 3: mandatory null checks (hard failure)
        (symbol is null or sector is null) as flag_missing_required_field,

        -- Step 10: currency validation (hard failure - pipeline assumes
        -- USD-denominated US equities throughout)
        (currency is not null and currency != 'USD') as flag_unexpected_currency,

        -- Step 6 (adapted "amount validation"): market cap must be
        -- positive to be meaningful (hard failure - broken data if not)
        (market_cap is not null and market_cap <= 0) as flag_invalid_market_cap,

        -- Logical consistency: 52-week high can never be below the low
        -- (hard failure - impossible data, same idea as OHLC check)
        (week_52_high is not null and week_52_low is not null
         and week_52_high < week_52_low) as flag_52week_inconsistent,

        -- Step 5 (adapted "transaction type" concept): sector must be
        -- one of our known values (soft flag - schema drift signal)
        (sector is not null and sector not in (
            'TECHNOLOGY', 'FINANCIAL SERVICES', 'ENERGY', 'HEALTHCARE',
            'LIFE SCIENCES', 'MANUFACTURING', 'TRADE & SERVICES'
        )) as flag_unexpected_sector,

        -- Soft flag: negative P/E is real (company reporting losses),
        -- worth surfacing, not an error
        (trailing_pe is not null and trailing_pe < 0) as flag_negative_pe,

        -- Soft flag: extreme/outlier profit margin, worth a second look
        (profit_margin is not null and abs(profit_margin) > 5) as flag_extreme_profit_margin,

        -- Step 7 (adapted "date validation"): fundamentals data more
        -- than 2 years stale suggests this symbol needs a fresh pull
        (latest_quarter is not null
         and latest_quarter < add_months(current_date(), -24)) as flag_stale_fundamentals

    from deduplicated

)

select
    *,
    (flag_missing_required_field
     or flag_unexpected_currency
     or flag_invalid_market_cap
     or flag_52week_inconsistent) as is_quarantined
from flagged