"""
Databricks connection helper for the Streamlit dashboard.

Centralizes query execution so every dashboard section calls one
function instead of each managing its own connection. Uses Streamlit's
built-in caching so repeated queries within a session don't re-hit
Databricks every time a filter changes - only on first load or after
the cache expires.

Credentials are read from Streamlit secrets (st.secrets) when deployed
on Streamlit Community Cloud, or from environment variables (.env) when
running locally - whichever is available, so the same code works in
both environments without changes.
"""

import os
import pandas as pd
import streamlit as st
from databricks import sql
from dotenv import load_dotenv

load_dotenv()


def _get_credential(key: str) -> str:
    """Try Streamlit secrets first (cloud deployment), fall back to
    environment variables (local development). st.secrets raises
    StreamlitSecretNotFoundError (not just a missing-key False) when no
    secrets.toml file exists at all, which is the normal case for local
    development - so that specific case is caught and treated as "not
    available" rather than a real error."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ[key]


@st.cache_resource
def get_connection():
    """Open one Databricks SQL connection, reused across the session
    rather than reconnecting on every query."""
    host = _get_credential("DATABRICKS_HOST").replace("https://", "")
    http_path = _get_credential("DATABRICKS_HTTP_PATH")
    token = _get_credential("DATABRICKS_TOKEN")

    return sql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token,
    )


@st.cache_data(ttl=600)  # cache results for 10 minutes
def run_query(query: str) -> pd.DataFrame:
    """Run a SQL query against Databricks and return a pandas DataFrame.
    Cached so switching between dashboard tabs doesn't re-query
    Databricks for data that hasn't changed."""
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=columns)