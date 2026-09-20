"""
Bronze layer ingestion script - COMPANY FUNDAMENTALS (run rarely, not daily).

Pulls company overview data (sector, industry, market cap, P/E ratio) from
Alpha Vantage's OVERVIEW endpoint and lands raw JSON into a Databricks Volume.

Why this is a SEPARATE script from fetch_prices.py:
- Fundamentals barely change day to day (sector, industry basically never
  change; market cap/P/E drift slowly).
- Re-fetching this daily would burn 9 of our 25 free API calls/day for
  almost no new information.
- Scheduled weekly via Airflow (company_overview_monthly DAG), not daily.

Design principles (same as fetch_prices.py):
- No transformation here, raw landing only.
- Idempotent: overwrite=True means re-running replaces the file, no dupes.
- Partitioned by the date it was fetched, so Silver can see how fresh
  the fundamentals data is.
- Quota-safety: stops the whole run immediately if the daily API limit
  is hit, rather than burning further calls against an exhausted quota.
"""

import os
import sys
import time
import json
import logging
import io
from datetime import date

import requests
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.environ["ALPHA_VANTAGE_API_KEY"]
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

VOLUME_PATH = "/Volumes/finance_medallion_pipeline/bronze__raw_layer/fetch_raw_company_overview"

TICKERS = [
    "AAPL", "MSFT", "NVDA",
    "JPM", "BAC",
    "XOM", "CVX",
    "JNJ", "PFE",
]

SECONDS_BETWEEN_CALLS = 13

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("bronze_overview_ingestion")


class QuotaExceededError(Exception):
    """Raised when Alpha Vantage reports the daily call limit has been hit."""
    pass


def fetch_company_overview(symbol: str) -> dict:
    """Call Alpha Vantage OVERVIEW for a single ticker."""
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    info_text = str(data.get("Information", "")) + str(data.get("Note", ""))
    if "rate limit" in info_text.lower() or "requests per day" in info_text.lower():
        raise QuotaExceededError(info_text)

    if not data or "Symbol" not in data:
        raise ValueError(f"Unexpected/empty response for {symbol}: {data}")

    return data


def write_to_volume(client: WorkspaceClient, folder_date: str, symbol: str, payload: dict) -> None:
    """Write raw JSON for one ticker's fundamentals into the dated partition folder."""
    file_path = f"{VOLUME_PATH}/{folder_date}/{symbol}.json"
    content = json.dumps(payload, indent=2).encode("utf-8")
    client.files.upload(file_path, io.BytesIO(content), overwrite=True)


def main():
    folder_date = date.today().isoformat()
    client = WorkspaceClient()

    logger.info(
        "Starting fundamentals ingestion for %s (%d tickers).",
        folder_date, len(TICKERS),
    )

    succeeded, failed = [], []
    quota_hit = False

    for i, symbol in enumerate(TICKERS):
        try:
            logger.info("Fetching overview for %s ...", symbol)
            payload = fetch_company_overview(symbol)
            write_to_volume(client, folder_date, symbol, payload)
            succeeded.append(symbol)
            logger.info("Wrote %s/%s/%s.json", VOLUME_PATH, folder_date, symbol)
        except QuotaExceededError as exc:
            # Fixed: message now has exactly 3 %s placeholders matching
            # the 3 arguments passed - the previous mismatch (2 vs 3)
            # caused a secondary logging crash on top of the real error.
            logger.error(
                "Daily API quota exhausted while fetching %s. Stopping run. "
                "Remaining tickers not attempted: %s. Reason: %s",
                symbol, TICKERS[i:], exc,
            )
            quota_hit = True
            break
        except Exception as exc:
            failed.append(symbol)
            logger.error("Failed to ingest overview for %s: %s", symbol, exc)

        if i < len(TICKERS) - 1:
            time.sleep(SECONDS_BETWEEN_CALLS)

    logger.info("Done. Succeeded: %d, Failed: %d", len(succeeded), len(failed))
    if failed:
        logger.warning("Failed tickers: %s", failed)
    if failed or quota_hit:
        sys.exit(1)


if __name__ == "__main__":
    main()