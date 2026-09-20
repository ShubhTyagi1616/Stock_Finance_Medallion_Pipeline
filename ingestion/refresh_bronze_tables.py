"""
Bronze layer refresh script.

Rebuilds the two Bronze Delta tables from whatever raw JSON files
currently sit in their respective Databricks Volumes. This is the
automated equivalent of the CREATE OR REPLACE TABLE ... read_files(...)
SQL we ran manually in the SQL Editor during development.

Must run AFTER fetch_prices.py (and, rarely, fetch_company_overview.py)
and BEFORE any dbt run - dbt only ever reads from these Delta tables,
never from the raw Volume files directly, so this step is the required
bridge between "new files landed" and "dbt can see them."

Uses the Databricks SDK's Statement Execution API - the same engine
the browser SQL Editor uses - rather than databricks-sql-connector,
which routes through a different execution path that doesn't fully
support read_files' named-argument syntax (format => 'json' etc.),
as discovered while building this script.
"""

import os
import sys
import re
import logging

from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

load_dotenv()

CATALOG = "finance_medallion_pipeline"
BRONZE_SCHEMA = "bronze__raw_layer"

HTTP_PATH = os.environ["DATABRICKS_HTTP_PATH"]  # e.g. /sql/1.0/warehouses/fffda0dd754568e4
WAREHOUSE_ID = re.search(r"warehouses/([a-zA-Z0-9]+)", HTTP_PATH).group(1)

REFRESH_STATEMENTS = {
    "raw_daily_prices": f"""
        CREATE OR REPLACE TABLE {CATALOG}.{BRONZE_SCHEMA}.raw_daily_prices AS
        SELECT raw_json
        FROM read_files(
          '/Volumes/{CATALOG}/{BRONZE_SCHEMA}/raw_stock_data/',
          format => 'json',
          multiLine => true,
          singleVariantColumn => 'raw_json'
        )
    """,
    "raw_company_overview": f"""
        CREATE OR REPLACE TABLE {CATALOG}.{BRONZE_SCHEMA}.raw_company_overview AS
        SELECT raw_json
        FROM read_files(
          '/Volumes/finance_medallion_pipeline/bronze__raw_layer/fetch_raw_company_overview',
          format => 'json',
          multiLine => true,
          singleVariantColumn => 'raw_json'
        )
    """,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("bronze_table_refresh")


def get_row_count(client: WorkspaceClient, table_name: str) -> int:
    """Query the actual row count of a table - used to verify a refresh
    genuinely landed data, rather than trusting a 'succeeded' status alone."""
    result = client.statement_execution.execute_statement(
        statement=f"SELECT count(*) as cnt FROM {CATALOG}.{BRONZE_SCHEMA}.{table_name}",
        warehouse_id=WAREHOUSE_ID,
        wait_timeout="30s",
    )
    return int(result.result.data_array[0][0])


def main():
    client = WorkspaceClient()  # picks up host/token from .env or .databrickscfg

    for table_name, statement in REFRESH_STATEMENTS.items():
        try:
            logger.info("Refreshing %s ...", table_name)
            result = client.statement_execution.execute_statement(
                statement=statement,
                warehouse_id=WAREHOUSE_ID,
                wait_timeout="50s",
            )
            if result.status.state != StatementState.SUCCEEDED:
                raise RuntimeError(f"Statement did not succeed: {result.status}")

            # Verify: don't just trust the "succeeded" status - confirm
            # real rows actually landed in the table.
            row_count = get_row_count(client, table_name)
            if row_count == 0:
                raise RuntimeError(
                    f"{table_name} reports SUCCEEDED but has 0 rows - "
                    f"refusing to treat this as a real success"
                )
            logger.info("Refreshed %s successfully (%d rows)", table_name, row_count)

        except Exception as exc:
            logger.error("Failed to refresh %s: %s", table_name, exc)
            sys.exit(1)  # non-zero exit so Airflow marks the task failed

    logger.info("Bronze table refresh complete.")


if __name__ == "__main__":
    main()