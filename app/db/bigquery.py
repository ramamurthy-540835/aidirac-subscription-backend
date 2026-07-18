from functools import lru_cache

from google.cloud import bigquery

from app.core.config import get_settings


@lru_cache
def get_bigquery_client() -> bigquery.Client:
    settings = get_settings()
    return bigquery.Client(project=settings.gcp_project_id)


def table_id(table_name: str) -> str:
    settings = get_settings()
    client = get_bigquery_client()
    return f"{client.project}.{settings.bigquery_dataset}.{table_name}"


def qualified_table(table_name: str) -> str:
    return f"`{table_id(table_name)}`"


def ensure_bigquery_schema() -> None:
    settings = get_settings()
    client = get_bigquery_client()
    dataset_ref = bigquery.DatasetReference(client.project, settings.bigquery_dataset)
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = settings.bigquery_location
    client.create_dataset(dataset, exists_ok=True)

    tables = {
        "subscription_plans": [
            bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("plan_code", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("description", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("monthly_price_usd", "NUMERIC"),
            bigquery.SchemaField("monthly_token_limit", "INTEGER"),
            bigquery.SchemaField("features", "STRING", mode="REPEATED"),
            bigquery.SchemaField("pricing_label", "STRING"),
            bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED"),
            bigquery.SchemaField("display_order", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
        ],
        "user_subscriptions": [
            bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("plan_code", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("billing_cycle", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("token_allowance_snapshot", "INTEGER"),
            bigquery.SchemaField("started_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("current_period_start", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("current_period_end", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("cancelled_at", "TIMESTAMP"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
        ],
        "token_usage": [
            bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("subscription_id", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("request_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("model_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("prompt_tokens", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("completion_tokens", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("total_tokens", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("usage_period_start", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("usage_period_end", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("metadata_json", "JSON", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ],
    }

    for table_name, schema in tables.items():
        table = bigquery.Table(f"{client.project}.{settings.bigquery_dataset}.{table_name}", schema=schema)
        client.create_table(table, exists_ok=True)
