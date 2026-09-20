# Extends Airflow's official image with the packages our pipeline tasks
# need: requests + python-dotenv for the ingestion scripts, databricks-sdk
# for talking to Databricks, dbt-databricks for running dbt from inside
# the container.

FROM apache/airflow:3.3.2

USER airflow

RUN pip install --no-cache-dir \
    requests \
    python-dotenv \
    databricks-sdk \
    dbt-databricks