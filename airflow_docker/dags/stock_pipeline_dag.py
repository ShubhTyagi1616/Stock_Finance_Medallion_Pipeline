"""
Daily medallion pipeline DAG.

Chains together the full Bronze -> Silver -> Gold flow, in the order
that matters: each stage only starts after the previous one succeeds.
If Silver's tests fail, Gold never runs - this is the "quality gate
between layers" from the original project plan, enforced structurally
by task dependencies rather than by a human remembering the right order.

Company overview refresh is intentionally NOT part of this daily DAG -
see overview_refresh_dag.py, scheduled separately and much less often,
since fundamentals data barely changes day to day.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

from utils.alerts import on_failure_alert

DBT_PROJECT_DIR = "/opt/airflow/dbt_project"
INGESTION_DIR = "/opt/airflow/ingestion"
ENV_FILE = "/opt/airflow/.env"

# Load the mounted .env file's variables into the shell before each
# command. Using `set -a; source ...; set +a` instead of
# `export $(... | xargs)` since the latter breaks on values containing
# special characters or files with Windows-style line endings.
ENV_PREFIX = f"set -a && source {ENV_FILE} && set +a &&"

default_args = {
    "owner": "shubham",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": on_failure_alert,
}

with DAG(
    dag_id="stock_pipeline_daily",
    description="Bronze -> Silver -> Gold daily pipeline for stock market data",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 9, 1),
    catchup=False,
    tags=["finance", "medallion", "daily"],
) as dag:

    fetch_prices = BashOperator(
        task_id="fetch_prices",
        bash_command=f"{ENV_PREFIX} python {INGESTION_DIR}/fetch_prices.py",
    )

    refresh_bronze_tables = BashOperator(
        task_id="refresh_bronze_tables",
        bash_command=f"{ENV_PREFIX} python {INGESTION_DIR}/refresh_bronze_tables.py",
    )

    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command=f"{ENV_PREFIX} cd {DBT_PROJECT_DIR} && dbt run --select silver --profiles-dir {DBT_PROJECT_DIR}",
    )

    dbt_test_silver = BashOperator(
        task_id="dbt_test_silver",
        bash_command=f"{ENV_PREFIX} cd {DBT_PROJECT_DIR} && dbt test --select silver --exclude tag:gold --profiles-dir {DBT_PROJECT_DIR}",
    )

    dbt_run_gold = BashOperator(
        task_id="dbt_run_gold",
        bash_command=f"{ENV_PREFIX} cd {DBT_PROJECT_DIR} && dbt run --select gold --profiles-dir {DBT_PROJECT_DIR}",
    )

    dbt_test_gold = BashOperator(
        task_id="dbt_test_gold",
        bash_command=f"{ENV_PREFIX} cd {DBT_PROJECT_DIR} && dbt test --select gold --profiles-dir {DBT_PROJECT_DIR}",
    )

    # Linear chain: each stage gates the next. A failure anywhere stops
    # the chain - Gold never builds on top of unvalidated Silver data.
    fetch_prices >> refresh_bronze_tables >> dbt_run_silver >> dbt_test_silver >> dbt_run_gold >> dbt_test_gold