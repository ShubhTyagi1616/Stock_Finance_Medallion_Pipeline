/*
  Silver: company_overview_quarantine

  Holds rows that failed a HARD check: missing symbol/sector, non-USD
  currency, invalid (non-positive) market cap, or an impossible
  52-week high/low relationship.
*/

select
    symbol,
    company_name,
    sector,
    currency,
    market_cap,
    week_52_high,
    week_52_low,
    flag_missing_required_field,
    flag_unexpected_currency,
    flag_invalid_market_cap,
    flag_52week_inconsistent,
    current_timestamp() as quarantined_at
from {{ ref('int_company_overview_flagged') }}
where is_quarantined