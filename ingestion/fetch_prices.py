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

VOLUME_PATH = "/Volumes/finance_medallion_pipeline/bronze__raw_layer/raw_stock_data"

TICKERS = [
    "AAPL", "MSFT", "NVDA",   # Tech 
    "JPM", "BAC",             # Finance
    "XOM", "CVX",             # Energy
    "JNJ", "PFE",             # Healthcare
]


SECONDS_BETWEEN_CALLS = 13   # ~4.6 CALLS/MINUTE, SAFELY UNDER THE 5 CALLS/MINUTE LIMIT OF ALPHA VANTAGE API

# Company fundamentals (sector, market cap, P/E) barely change day to day,
# so they are intentionally NOT fetched here. See fetch_company_overview.py,
# which is meant to be run once, then only occasionally to refresh.
# This keeps daily usage at 9 calls/day instead of 18, leaving more buffer
# under the 25/day cap for retries.

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("bronze_ingestion_daily_prices")


# CORE FUNCTIONS:
class QuotaExceededError(Exception):
    """quota hit when any call fails and immediately stop the remaining calls """
    pass


def fetch_daily_prices(symbol: str) -> dict:
    """Call Alpha vantage TIME_SERIES_DAILY for a single ticker."""
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    info_text = str(data.get("Information", "")) + str(data.get("Note", ""))
    if "rate limit" in info_text.lower() or "requests per day" in info_text.lower():
        raise QuotaExceededError(info_text)

    if "Time Series (Daily)" not in data:
        raise ValueError(f"Unexpected response for {symbol}: {data}")

    return data 


def already_fetched(client: WorkspaceClient, folder_date: str, symbol: str) -> bool:
    """check if this ticker's file already exists for today - avoids burning API QUOTA """
    file_path = f"{VOLUME_PATH}/{folder_date}/{symbol}.json"
    try:
        client.files.get_metadata(file_path)
        return True
    except Exception:
        return False



def write_to_volume(client: WorkspaceClient, folder_date: str, symbol: str, payload: dict) -> None:
    """Write raw JSON for one ticker into the dated partition folder."""
    file_path = f"{VOLUME_PATH}/{folder_date}/{symbol}.json"
    content = json.dumps(payload, indent=2).encode("utf-8")

    client.files.upload(file_path, io.BytesIO(content), overwrite=True)   # this step is for idempotency: same date replaces that day's file instead of erroring or duplicating.



def main():

     # Targeted backfill/recovery run (e.g. yesterday's failures):
    #   python fetch_prices.py --date 2026-09-09 --tickers CVX JNJ PFE
    #   -> lets you re-target a SPECIFIC past date's folder and ONLY the
    #      tickers that failed, without burning quota re-checking the rest
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Override folder date, format YYYY-MM-DD")
    parser.add_argument("--tickers", nargs="+", default=None, help="Override ticker list")
    args = parser.parse_args()


    folder_date = args.date or date.today().isoformat()
    tickers = args.tickers or TICKERS
    client = WorkspaceClient()

    logger.info("Starting Bronze ingestion for %s (%d tickers)", folder_date, len(tickers)) 

    succeeded, failed = [], []
    quota_hit = False


    for i, symbol in enumerate(tickers):
        if already_fetched(client, folder_date, symbol):
            logger.info("Skipping %s - already fetched", symbol)
            succeeded.append(symbol)
            continue

        try:
            logger.info("Fetching %s ...", symbol)
            payload = fetch_daily_prices(symbol)
            write_to_volume(client, folder_date, symbol, payload)
            succeeded.append(symbol)
            logger.info("Wrote %s/%s/%s.json", VOLUME_PATH, folder_date, symbol)

        except QuotaExceededError as err:
            logger.error(
                "Daily API quota exhausted while fetching %s. Stopping run "
                "attempting: %s. Reason: %s",
                symbol, tickers[i:], err,
            )
            quota_hit = True
            break  # stop the loop, don't try to fetch any more tickers

        except Exception as err:
            failed.append(symbol)
            logger.error("Failed to ingest %s: %s", symbol, err)

        # respect rate limit between calls:
        if i < len(tickers) -1:
            time.sleep(SECONDS_BETWEEN_CALLS)


    logger.info("Done. Succeeded: %d, Failed: %d", len(succeeded), len(failed))
    if failed:
        logger.warning("Failed tickers: %s", failed)
    if quota_hit:
        logger.warning(
            "Run stopped early due to quota limit."
            "--date %s --tickers <remaining symbols> to finish",
            folder_date,
            )

    if failed or quota_hit:
        sys.exit(1)   # non-zero exit so Airflow can detect and alert on failure for CI/CD pipelines.

if __name__ == "__main__":
    main()

