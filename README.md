# AIDIRAC Subscription Backend

Standalone FastAPI backend service for AIDIRAC subscription plan management.

Phase 1 includes subscription plan management only. It does not include payments, users, authentication, user subscriptions, token consumption, or frontend changes.

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite for local development
- Uvicorn
- Pytest

## Project Structure

```text
app/
  api/
    dependencies.py
    router.py
  core/
    config.py
  db/
    base.py
    session.py
  models/
    subscription_plan.py
  repositories/
    subscription_plan_repository.py
  schemas/
    subscription_plan.py
  services/
    subscription_plan_service.py
  main.py
  seed.py
tests/
  conftest.py
  test_subscription_plans.py
.env.example
requirements.txt
README.md
```

## Local Setup

From Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Tests

```cmd
.venv\Scripts\activate
pytest
```

## Endpoints

- `GET /api/health`
- `GET /api/subscription-plans`
- `GET /api/subscription-plans/{plan_code}`
- `POST /api/subscription-plans`
- `PUT /api/subscription-plans/{plan_code}`
- `PATCH /api/subscription-plans/{plan_code}/status`

## Seeded Plans

On startup, the service creates database tables and upserts these plans:

| Plan | Price | Monthly token limit | Display order |
| --- | ---: | ---: | ---: |
| Student | 5.00 | 500000 | 1 |
| Plus | 20.00 | 3000000 | 2 |
| Pro | 75.00 | 15000000 | 3 |
| Enterprise | Contact Sales | Custom | 4 |

Enterprise uses `monthly_price_usd: null`, `monthly_token_limit: null`, and `pricing_label: "Contact Sales"`.

## Curl Examples

```cmd
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/subscription-plans
curl http://127.0.0.1:8000/api/subscription-plans/student
curl -X POST http://127.0.0.1:8000/api/subscription-plans -H "Content-Type: application/json" -d "{\"plan_code\":\"team\",\"name\":\"Team\",\"description\":\"Shared usage for teams.\",\"monthly_price_usd\":\"150.00\",\"monthly_token_limit\":30000000,\"features\":[\"Shared workspace\",\"Team support\"],\"is_active\":true,\"display_order\":5}"
curl -X PUT http://127.0.0.1:8000/api/subscription-plans/team -H "Content-Type: application/json" -d "{\"name\":\"Team Plus\",\"description\":\"Updated shared usage for teams.\",\"monthly_price_usd\":\"175.00\",\"monthly_token_limit\":35000000,\"features\":[\"Shared workspace\",\"Priority support\"],\"is_active\":true,\"display_order\":5}"
curl -X PATCH http://127.0.0.1:8000/api/subscription-plans/team/status -H "Content-Type: application/json" -d "{\"is_active\":false}"
```
