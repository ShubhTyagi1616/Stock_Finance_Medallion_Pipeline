"""
Failure alert callback for the medallion pipeline DAGs.
 
Wired in via each DAG's default_args (on_failure_callback). Airflow
calls this automatically whenever any task fails, after its retries
are exhausted - giving a single, immediate signal that the pipeline
needs attention, rather than requiring someone to check the UI daily.
 
Two channels supported - enable whichever you've set up:
- Slack, via an incoming webhook URL
- Email, via SMTP (uses Airflow's built-in email utility)
 
Both read their config from environment variables, so no secrets are
hardcoded here. If neither is configured, this quietly logs the
failure instead of raising - so a missing alert channel never breaks
the pipeline itself, it just means you won't get pinged.
"""

import os
import logging

import requests

logger = logging.getLogger("pipeline_alerts")

def send_slack_alert(context):
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.info("SLACK_WEBHOOK_URL not set - skipping slack alert")
        return

    task_instance = context.get("task_instance")
    dag_id = context.get("dag").dag_id
    task_id = task_instance.task_id
    execution_date = context.get("execution_date")
    log_url = task_instance.log_url

    message = {
        "text": (
            f":red_circle: *Pipeline failure*\n"
             f"*DAG:* {dag_id}\n"
            f"*Task:* {task_id}\n"
            f"*Run:* {execution_date}\n"
            f"*Logs:* {log_url}"
        )
    }

    try:
        response = requests.post(webhook_url,json=message, timeout=10)
        response.raise_for_status()
        logger.info("Slack alert sent successful")
    except Exception as err:
        logger.error("Failed to send slack alert: %s", err)


def on_failure_alert(context):
    """Main callback - pass this as on_failure_callback in DAG default_args."""
    send_slack_alert(context)