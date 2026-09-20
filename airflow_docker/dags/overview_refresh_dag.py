"""
Monthly company fundamentals refresh DAG.

Runs fetch_company_overview.py + refreshes the raw_company_overview
Bronze table, then rebuilds Silver/Gold so the new fundamentals flow
through. Kept SEPARATE from the daily price pipeline (stock_pipeline_dag.py)
because sector, market cap, and other fundamentals barely change day to
day - refreshing them daily would waste Alpha Vantage's limited free
API quota for almost no new information.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

from utils.alerts import on_failure_alert

DBT_PROJECT_DIR = "/opt/airflow/dbt_project"
INGESTION_DIR = "/opt/airflow/ingestion"
ENV_FILE = "/opt/airflow/.env"

ENV_PREFIX = f"set -a && source {ENV_FILE} && set +a &&"

default_args = {
    "owner": "shubham",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": on_failure_alert,
}

with DAG(
    dag_id="company_overview_weekly",
    description="Weekly refresh of company fundamentals (sector, market cap, P/E, etc.)",
    default_args=default_args,
    schedule="@weekly",
    start_date=datetime(2026, 9, 1),
    catchup=False,
    tags=["finance", "medallion", "weekly"],
) as dag:

    fetch_overview = BashOperator(
        task_id="fetch_company_overview",
        bash_command=f"{ENV_PREFIX} python {INGESTION_DIR}/fetch_company_overview.py",
    )

    refresh_bronze_overview_table = BashOperator(
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

    fetch_overview >> refresh_bronze_overview_table >> dbt_run_silver >> dbt_test_silver >> dbt_run_gold >> dbt_test_gold