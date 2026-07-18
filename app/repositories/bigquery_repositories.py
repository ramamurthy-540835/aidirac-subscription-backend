from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from google.cloud import bigquery
from sqlalchemy.exc import IntegrityError

from app.db.bigquery import get_bigquery_client, qualified_table
from app.models.token_usage import TokenUsage
from app.models.user_subscription import UserSubscription
from app.schemas.subscription_plan import SubscriptionPlanCreate, SubscriptionPlanUpdate


class _NoopDb:
    def rollback(self) -> None:
        return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _rows(query: str, parameters: list | None = None) -> list[dict]:
    client = get_bigquery_client()
    job_config = bigquery.QueryJobConfig(query_parameters=parameters or [])
    return [dict(row) for row in client.query(query, job_config=job_config).result()]


def _one(query: str, parameters: list | None = None) -> dict | None:
    rows = _rows(query, parameters)
    return rows[0] if rows else None


def _next_id(table_name: str) -> int:
    row = _one(f"SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM {qualified_table(table_name)}")
    return int(row["next_id"])


def _entity(row: dict | None) -> SimpleNamespace | None:
    if row is None:
        return None
    data = dict(row)
    if isinstance(data.get("monthly_price_usd"), str):
        data["monthly_price_usd"] = Decimal(data["monthly_price_usd"])
    return SimpleNamespace(**data)


def _insert_subscription_plan(row: dict) -> None:
    _rows(
        f"""
        INSERT INTO {qualified_table('subscription_plans')}
        (id, plan_code, name, description, monthly_price_usd, monthly_token_limit, features, pricing_label, is_active, display_order, created_at, updated_at)
        VALUES (@id, @plan_code, @name, @description, @monthly_price_usd, @monthly_token_limit, @features, @pricing_label, @is_active, @display_order, @created_at, @updated_at)
        """,
        [
            bigquery.ScalarQueryParameter("id", "INT64", row["id"]),
            bigquery.ScalarQueryParameter("plan_code", "STRING", row["plan_code"]),
            bigquery.ScalarQueryParameter("name", "STRING", row["name"]),
            bigquery.ScalarQueryParameter("description", "STRING", row["description"]),
            bigquery.ScalarQueryParameter("monthly_price_usd", "NUMERIC", row["monthly_price_usd"]),
            bigquery.ScalarQueryParameter("monthly_token_limit", "INT64", row["monthly_token_limit"]),
            bigquery.ArrayQueryParameter("features", "STRING", row["features"]),
            bigquery.ScalarQueryParameter("pricing_label", "STRING", row["pricing_label"]),
            bigquery.ScalarQueryParameter("is_active", "BOOL", row["is_active"]),
            bigquery.ScalarQueryParameter("display_order", "INT64", row["display_order"]),
            bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", row["created_at"]),
            bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", row["updated_at"]),
        ],
    )


def _insert_user_subscription(row: dict) -> None:
    _rows(
        f"""
        INSERT INTO {qualified_table('user_subscriptions')}
        (id, user_id, plan_code, status, billing_cycle, token_allowance_snapshot, started_at, current_period_start, current_period_end, cancelled_at, created_at, updated_at)
        VALUES (@id, @user_id, @plan_code, @status, @billing_cycle, @token_allowance_snapshot, @started_at, @current_period_start, @current_period_end, @cancelled_at, @created_at, @updated_at)
        """,
        [
            bigquery.ScalarQueryParameter("id", "INT64", row["id"]),
            bigquery.ScalarQueryParameter("user_id", "STRING", row["user_id"]),
            bigquery.ScalarQueryParameter("plan_code", "STRING", row["plan_code"]),
            bigquery.ScalarQueryParameter("status", "STRING", row["status"]),
            bigquery.ScalarQueryParameter("billing_cycle", "STRING", row["billing_cycle"]),
            bigquery.ScalarQueryParameter("token_allowance_snapshot", "INT64", row["token_allowance_snapshot"]),
            bigquery.ScalarQueryParameter("started_at", "TIMESTAMP", row["started_at"]),
            bigquery.ScalarQueryParameter("current_period_start", "TIMESTAMP", row["current_period_start"]),
            bigquery.ScalarQueryParameter("current_period_end", "TIMESTAMP", row["current_period_end"]),
            bigquery.ScalarQueryParameter("cancelled_at", "TIMESTAMP", row["cancelled_at"]),
            bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", row["created_at"]),
            bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", row["updated_at"]),
        ],
    )


def _insert_token_usage(row: dict) -> None:
    _rows(
        f"""
        INSERT INTO {qualified_table('token_usage')}
        (id, event_id, user_id, subscription_id, request_type, model_name, prompt_tokens, completion_tokens, total_tokens, usage_period_start, usage_period_end, metadata_json, created_at)
        VALUES (@id, @event_id, @user_id, @subscription_id, @request_type, @model_name, @prompt_tokens, @completion_tokens, @total_tokens, @usage_period_start, @usage_period_end, PARSE_JSON(@metadata_json), @created_at)
        """,
        [
            bigquery.ScalarQueryParameter("id", "INT64", row["id"]),
            bigquery.ScalarQueryParameter("event_id", "STRING", row["event_id"]),
            bigquery.ScalarQueryParameter("user_id", "STRING", row["user_id"]),
            bigquery.ScalarQueryParameter("subscription_id", "INT64", row["subscription_id"]),
            bigquery.ScalarQueryParameter("request_type", "STRING", row["request_type"]),
            bigquery.ScalarQueryParameter("model_name", "STRING", row["model_name"]),
            bigquery.ScalarQueryParameter("prompt_tokens", "INT64", row["prompt_tokens"]),
            bigquery.ScalarQueryParameter("completion_tokens", "INT64", row["completion_tokens"]),
            bigquery.ScalarQueryParameter("total_tokens", "INT64", row["total_tokens"]),
            bigquery.ScalarQueryParameter("usage_period_start", "TIMESTAMP", row["usage_period_start"]),
            bigquery.ScalarQueryParameter("usage_period_end", "TIMESTAMP", row["usage_period_end"]),
            bigquery.ScalarQueryParameter("metadata_json", "STRING", row["metadata_json"]),
            bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", row["created_at"]),
        ],
    )


def _decimal_value(value):
    return str(value) if isinstance(value, Decimal) else value


class BigQuerySubscriptionPlanRepository:
    db = _NoopDb()

    def list(self, active_only: bool = False):
        where = "WHERE is_active = TRUE" if active_only else ""
        return [_entity(row) for row in _rows(f"SELECT * FROM {qualified_table('subscription_plans')} {where} ORDER BY display_order, id")]

    def get_by_plan_code(self, plan_code: str):
        return _entity(
            _one(
                f"SELECT * FROM {qualified_table('subscription_plans')} WHERE plan_code = @plan_code LIMIT 1",
                [bigquery.ScalarQueryParameter("plan_code", "STRING", plan_code.lower())],
            )
        )

    def create(self, payload: SubscriptionPlanCreate):
        if self.get_by_plan_code(payload.plan_code) is not None:
            raise IntegrityError("duplicate plan_code", None, None)
        now = _utc_now()
        row = payload.model_dump()
        row.update({"id": _next_id("subscription_plans"), "created_at": now.isoformat(), "updated_at": now.isoformat()})
        row["monthly_price_usd"] = _decimal_value(row["monthly_price_usd"])
        _insert_subscription_plan(row)
        return self.get_by_plan_code(payload.plan_code)

    def update(self, plan, payload: SubscriptionPlanUpdate):
        values = payload.model_dump(exclude_unset=True)
        if not values:
            return plan
        updated = {**plan.__dict__, **values, "updated_at": _utc_now()}
        _rows(
            f"""
            UPDATE {qualified_table('subscription_plans')}
            SET name = @name, description = @description, monthly_price_usd = @monthly_price_usd,
                monthly_token_limit = @monthly_token_limit, features = @features,
                pricing_label = @pricing_label, is_active = @is_active, display_order = @display_order,
                updated_at = @updated_at
            WHERE id = @id
            """,
            [
                bigquery.ScalarQueryParameter("id", "INT64", updated["id"]),
                bigquery.ScalarQueryParameter("name", "STRING", updated["name"]),
                bigquery.ScalarQueryParameter("description", "STRING", updated["description"]),
                bigquery.ScalarQueryParameter("monthly_price_usd", "NUMERIC", _decimal_value(updated["monthly_price_usd"])),
                bigquery.ScalarQueryParameter("monthly_token_limit", "INT64", updated["monthly_token_limit"]),
                bigquery.ArrayQueryParameter("features", "STRING", updated["features"]),
                bigquery.ScalarQueryParameter("pricing_label", "STRING", updated["pricing_label"]),
                bigquery.ScalarQueryParameter("is_active", "BOOL", updated["is_active"]),
                bigquery.ScalarQueryParameter("display_order", "INT64", updated["display_order"]),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", updated["updated_at"]),
            ],
        )
        return self.get_by_plan_code(plan.plan_code)

    def update_status(self, plan, is_active: bool):
        _rows(
            f"UPDATE {qualified_table('subscription_plans')} SET is_active = @is_active, updated_at = @updated_at WHERE id = @id",
            [
                bigquery.ScalarQueryParameter("id", "INT64", plan.id),
                bigquery.ScalarQueryParameter("is_active", "BOOL", is_active),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", _utc_now()),
            ],
        )
        return self.get_by_plan_code(plan.plan_code)

    def upsert_seed(self, payload: dict):
        plan = self.get_by_plan_code(payload["plan_code"])
        if plan is None:
            return self.create(SubscriptionPlanCreate(**payload))
        return self.update(plan, SubscriptionPlanUpdate(**payload))


class BigQueryUserSubscriptionRepository:
    def _get_by_user_and_status(self, user_id: str, statuses: list[str]):
        return _entity(
            _one(
                f"""
                SELECT * FROM {qualified_table('user_subscriptions')}
                WHERE user_id = @user_id AND status IN UNNEST(@statuses)
                ORDER BY id DESC
                LIMIT 1
                """,
                [
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                    bigquery.ArrayQueryParameter("statuses", "STRING", statuses),
                ],
            )
        )

    def get_current_by_user_id(self, user_id: str):
        return self._get_by_user_and_status(user_id, ["active", "pending"])

    def get_active_by_user_id(self, user_id: str):
        return self._get_by_user_and_status(user_id, ["active"])

    def get_latest_by_user_id(self, user_id: str):
        return _entity(
            _one(
                f"SELECT * FROM {qualified_table('user_subscriptions')} WHERE user_id = @user_id ORDER BY id DESC LIMIT 1",
                [bigquery.ScalarQueryParameter("user_id", "STRING", user_id)],
            )
        )

    def create(self, subscription: UserSubscription):
        now = _utc_now()
        row = {
            "id": _next_id("user_subscriptions"),
            "user_id": subscription.user_id,
            "plan_code": subscription.plan_code,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "token_allowance_snapshot": subscription.token_allowance_snapshot,
            "started_at": subscription.started_at.isoformat(),
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
            "cancelled_at": subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        _insert_user_subscription(row)
        return self.get_latest_by_user_id(subscription.user_id)

    def update(self, subscription):
        _rows(
            f"""
            UPDATE {qualified_table('user_subscriptions')}
            SET plan_code = @plan_code, status = @status, billing_cycle = @billing_cycle,
                token_allowance_snapshot = @token_allowance_snapshot, started_at = @started_at,
                current_period_start = @current_period_start, current_period_end = @current_period_end,
                cancelled_at = @cancelled_at, updated_at = @updated_at
            WHERE id = @id
            """,
            [
                bigquery.ScalarQueryParameter("id", "INT64", subscription.id),
                bigquery.ScalarQueryParameter("plan_code", "STRING", subscription.plan_code),
                bigquery.ScalarQueryParameter("status", "STRING", subscription.status),
                bigquery.ScalarQueryParameter("billing_cycle", "STRING", subscription.billing_cycle),
                bigquery.ScalarQueryParameter("token_allowance_snapshot", "INT64", subscription.token_allowance_snapshot),
                bigquery.ScalarQueryParameter("started_at", "TIMESTAMP", subscription.started_at),
                bigquery.ScalarQueryParameter("current_period_start", "TIMESTAMP", subscription.current_period_start),
                bigquery.ScalarQueryParameter("current_period_end", "TIMESTAMP", subscription.current_period_end),
                bigquery.ScalarQueryParameter("cancelled_at", "TIMESTAMP", subscription.cancelled_at),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", _utc_now()),
            ],
        )
        return self.get_latest_by_user_id(subscription.user_id)


class BigQueryTokenUsageRepository:
    db = _NoopDb()

    def get_by_event_id(self, event_id: str):
        return _entity(
            _one(
                f"SELECT * FROM {qualified_table('token_usage')} WHERE event_id = @event_id LIMIT 1",
                [bigquery.ScalarQueryParameter("event_id", "STRING", event_id)],
            )
        )

    def sum_for_subscription_period(self, subscription_id: int, period_start: datetime, period_end: datetime) -> int:
        row = _one(
            f"""
            SELECT COALESCE(SUM(total_tokens), 0) AS total
            FROM {qualified_table('token_usage')}
            WHERE subscription_id = @subscription_id
              AND usage_period_start = @period_start
              AND usage_period_end = @period_end
            """,
            [
                bigquery.ScalarQueryParameter("subscription_id", "INT64", subscription_id),
                bigquery.ScalarQueryParameter("period_start", "TIMESTAMP", period_start),
                bigquery.ScalarQueryParameter("period_end", "TIMESTAMP", period_end),
            ],
        )
        return int(row["total"])

    def list_for_user(self, user_id: str):
        return [
            _entity(row)
            for row in _rows(
                f"SELECT * FROM {qualified_table('token_usage')} WHERE user_id = @user_id ORDER BY created_at DESC, id DESC",
                [bigquery.ScalarQueryParameter("user_id", "STRING", user_id)],
            )
        ]

    def create(self, usage: TokenUsage):
        if self.get_by_event_id(usage.event_id) is not None:
            raise IntegrityError("duplicate event_id", None, None)
        now = _utc_now()
        row = {
            "id": _next_id("token_usage"),
            "event_id": usage.event_id,
            "user_id": usage.user_id,
            "subscription_id": usage.subscription_id,
            "request_type": usage.request_type,
            "model_name": usage.model_name,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "usage_period_start": usage.usage_period_start.isoformat(),
            "usage_period_end": usage.usage_period_end.isoformat(),
            "metadata_json": __import__("json").dumps(usage.metadata_json),
            "created_at": now.isoformat(),
        }
        _insert_token_usage(row)
        return self.get_by_event_id(usage.event_id)
