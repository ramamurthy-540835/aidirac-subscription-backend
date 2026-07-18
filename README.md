# AIDIRAC Subscription Backend

FastAPI backend for AIDIRAC subscription plans, user subscriptions, and token usage quota tracking.

The service can run with SQLite for local development and BigQuery for the deployed Cloud Run environment.

## Live Service

Cloud Run URL:

```text
https://aidirac-subscription-backend-1035117862188.us-central1.run.app
```

Health check:

```bash
curl https://aidirac-subscription-backend-1035117862188.us-central1.run.app/api/health
```

Expected response:

```json
{"status":"ok"}
```

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy with SQLite for local development
- BigQuery for deployed storage
- Cloud Run
- Pytest

## Environment

Local defaults use SQLite:

```env
APP_ENV=local
DATABASE_BACKEND=sqlalchemy
DATABASE_URL=sqlite:///./aidirac_subscription.db
```

Cloud Run uses BigQuery:

```env
APP_ENV=production
DATABASE_BACKEND=bigquery
GCP_PROJECT_ID=ctoteam
BIGQUERY_DATASET=aidirac_subscription
BIGQUERY_LOCATION=US
```

## BigQuery Tables

Project:

```text
ctoteam
```

Dataset:

```text
ctoteam.aidirac_subscription
```

Tables:

| Table | Purpose |
| --- | --- |
| `subscription_plans` | Plan catalog and pricing metadata |
| `user_subscriptions` | Current and historical user subscription state |
| `token_usage` | Token usage events tied to a subscription period |

### `subscription_plans`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `INT64` | Plan row id |
| `plan_code` | `STRING` | Unique code, for example `student` |
| `name` | `STRING` | Display name |
| `description` | `STRING` | Plan description |
| `monthly_price_usd` | `NUMERIC` | Null for custom pricing |
| `monthly_token_limit` | `INT64` | Null means unlimited/custom |
| `features` | `ARRAY<STRING>` | Feature list |
| `pricing_label` | `STRING` | For labels like `Contact Sales` |
| `is_active` | `BOOL` | Whether the plan can be selected |
| `display_order` | `INT64` | Sort order |
| `created_at` | `TIMESTAMP` | Created timestamp |
| `updated_at` | `TIMESTAMP` | Updated timestamp |

Seeded rows:

| Plan code | Price | Monthly token limit | Status |
| --- | ---: | ---: | --- |
| `student` | 5.00 | 500000 | active |
| `plus` | 20.00 | 3000000 | active |
| `pro` | 75.00 | 15000000 | active |
| `enterprise` | Contact Sales | Custom | active |

### `user_subscriptions`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `INT64` | Subscription row id |
| `user_id` | `STRING` | Application user id |
| `plan_code` | `STRING` | Selected plan code |
| `status` | `STRING` | `pending`, `active`, `past_due`, `cancelled`, `expired` |
| `billing_cycle` | `STRING` | `monthly` or `yearly` |
| `token_allowance_snapshot` | `INT64` | Token limit copied from plan at subscription time |
| `started_at` | `TIMESTAMP` | Subscription start |
| `current_period_start` | `TIMESTAMP` | Current quota period start |
| `current_period_end` | `TIMESTAMP` | Current quota period end |
| `cancelled_at` | `TIMESTAMP` | Cancellation timestamp |
| `created_at` | `TIMESTAMP` | Created timestamp |
| `updated_at` | `TIMESTAMP` | Updated timestamp |

### `token_usage`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `INT64` | Usage row id |
| `event_id` | `STRING` | Idempotency key for usage event |
| `user_id` | `STRING` | Application user id |
| `subscription_id` | `INT64` | Subscription id used for quota |
| `request_type` | `STRING` | Usage category |
| `model_name` | `STRING` | Model used |
| `prompt_tokens` | `INT64` | Prompt tokens |
| `completion_tokens` | `INT64` | Completion tokens |
| `total_tokens` | `INT64` | Prompt plus completion |
| `usage_period_start` | `TIMESTAMP` | Quota period start |
| `usage_period_end` | `TIMESTAMP` | Quota period end |
| `metadata_json` | `JSON` | Extra event metadata |
| `created_at` | `TIMESTAMP` | Created timestamp |

## API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/subscription-plans` | List plans |
| `GET` | `/api/subscription-plans/{plan_code}` | Get one plan |
| `POST` | `/api/subscription-plans` | Create a plan |
| `PUT` | `/api/subscription-plans/{plan_code}` | Update a plan |
| `PATCH` | `/api/subscription-plans/{plan_code}/status` | Activate/deactivate a plan |
| `POST` | `/api/user-subscriptions` | Create a user subscription |
| `GET` | `/api/user-subscriptions/{user_id}` | Get latest user subscription |
| `PATCH` | `/api/user-subscriptions/{user_id}/cancel` | Cancel current subscription |
| `PATCH` | `/api/user-subscriptions/{user_id}/change-plan` | Change current plan |
| `POST` | `/api/token-usage/consume` | Record token usage |
| `GET` | `/api/token-usage/{user_id}/summary` | Get usage summary |
| `GET` | `/api/token-usage/{user_id}/events` | List usage events |
| `GET` | `/api/token-usage/{user_id}/quota-check` | Check quota before consuming |

## Test The Live Deployment

Set the base URL:

```bash
BASE_URL="https://aidirac-subscription-backend-1035117862188.us-central1.run.app"
```

List plans:

```bash
curl "$BASE_URL/api/subscription-plans"
```

Get one plan:

```bash
curl "$BASE_URL/api/subscription-plans/student"
```

Create a test user subscription:

```bash
curl -X POST "$BASE_URL/api/user-subscriptions" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user-001","plan_code":"student","billing_cycle":"monthly"}'
```

Check quota:

```bash
curl "$BASE_URL/api/token-usage/test-user-001/quota-check?requested_tokens=1200"
```

Consume token usage:

```bash
curl -X POST "$BASE_URL/api/token-usage/consume" \
  -H "Content-Type: application/json" \
  -d '{"event_id":"evt-test-001","user_id":"test-user-001","request_type":"chat","model_name":"gpt-4.1-mini","prompt_tokens":800,"completion_tokens":400,"metadata":{"source":"readme-test"}}'
```

Get usage summary:

```bash
curl "$BASE_URL/api/token-usage/test-user-001/summary"
```

List usage events:

```bash
curl "$BASE_URL/api/token-usage/test-user-001/events"
```

Cancel test subscription:

```bash
curl -X PATCH "$BASE_URL/api/user-subscriptions/test-user-001/cancel"
```

Use unique `user_id` and `event_id` values when repeating tests. Duplicate active subscriptions return `409`, and duplicate usage events return `409`.

## Query BigQuery Directly

List plans:

```bash
bq query --project_id=ctoteam --use_legacy_sql=false \
  'SELECT plan_code, name, monthly_price_usd, monthly_token_limit, is_active
   FROM `ctoteam.aidirac_subscription.subscription_plans`
   ORDER BY display_order'
```

Inspect test subscriptions:

```bash
bq query --project_id=ctoteam --use_legacy_sql=false \
  'SELECT user_id, plan_code, status, billing_cycle, current_period_start, current_period_end
   FROM `ctoteam.aidirac_subscription.user_subscriptions`
   ORDER BY created_at DESC
   LIMIT 20'
```

Inspect usage events:

```bash
bq query --project_id=ctoteam --use_legacy_sql=false \
  'SELECT event_id, user_id, model_name, total_tokens, created_at
   FROM `ctoteam.aidirac_subscription.token_usage`
   ORDER BY created_at DESC
   LIMIT 20'
```

## Local Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Run tests:

```bash
.venv/bin/python -m pytest
```

## Deploy

```bash
gcloud run deploy aidirac-subscription-backend \
  --source . \
  --project ctoteam \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_BACKEND=bigquery,GCP_PROJECT_ID=ctoteam,BIGQUERY_DATASET=aidirac_subscription,BIGQUERY_LOCATION=US
```
