from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription_plan import SubscriptionPlan


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_seeded_plans_are_listed_in_display_order(client: TestClient) -> None:
    response = client.get("/api/subscription-plans")

    assert response.status_code == 200
    plans = response.json()
    assert [plan["plan_code"] for plan in plans] == ["student", "plus", "pro", "enterprise"]
    assert plans[0]["monthly_price_usd"] == "5.00"
    assert plans[0]["monthly_token_limit"] == 500000
    assert plans[3]["monthly_price_usd"] is None
    assert plans[3]["monthly_token_limit"] is None
    assert plans[3]["pricing_label"] == "Contact Sales"


def test_get_plan_by_code_is_case_insensitive(client: TestClient) -> None:
    response = client.get("/api/subscription-plans/Pro")

    assert response.status_code == 200
    assert response.json()["plan_code"] == "pro"
    assert response.json()["monthly_price_usd"] == "75.00"


def test_get_unknown_plan_returns_404(client: TestClient) -> None:
    response = client.get("/api/subscription-plans/unknown")

    assert response.status_code == 404
    assert response.json()["detail"] == "Subscription plan not found"


def test_create_plan(client: TestClient) -> None:
    payload = {
        "plan_code": "team",
        "name": "Team",
        "description": "Shared usage for small teams.",
        "monthly_price_usd": "150.00",
        "monthly_token_limit": 30000000,
        "features": ["Shared workspace", "Team support"],
        "is_active": True,
        "display_order": 5,
    }

    response = client.post("/api/subscription-plans", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["plan_code"] == "team"
    assert data["monthly_price_usd"] == "150.00"


def test_duplicate_plan_code_returns_409(client: TestClient) -> None:
    payload = {
        "plan_code": "student",
        "name": "Student Duplicate",
        "description": "Duplicate code.",
        "monthly_price_usd": "10.00",
        "monthly_token_limit": 100,
        "features": [],
        "is_active": True,
        "display_order": 10,
    }

    response = client.post("/api/subscription-plans", json=payload)

    assert response.status_code == 409


def test_custom_priced_plan_requires_pricing_label(client: TestClient) -> None:
    payload = {
        "plan_code": "custom",
        "name": "Custom",
        "description": "Custom pricing without label.",
        "monthly_price_usd": None,
        "monthly_token_limit": None,
        "features": [],
        "is_active": True,
        "display_order": 5,
    }

    response = client.post("/api/subscription-plans", json=payload)

    assert response.status_code == 422


def test_update_plan(client: TestClient) -> None:
    payload = {
        "name": "Plus Updated",
        "description": "Updated plus plan.",
        "monthly_price_usd": "25.00",
        "monthly_token_limit": 4000000,
        "features": ["Updated allowance"],
        "display_order": 2,
    }

    response = client.put("/api/subscription-plans/plus", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Plus Updated"
    assert data["monthly_price_usd"] == "25.00"
    assert data["monthly_token_limit"] == 4000000
    assert data["features"] == ["Updated allowance"]


def test_update_status(client: TestClient) -> None:
    response = client.patch("/api/subscription-plans/student/status", json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    active_response = client.get("/api/subscription-plans?active_only=true")
    assert [plan["plan_code"] for plan in active_response.json()] == ["plus", "pro", "enterprise"]


def test_seed_is_idempotent(db_session: Session) -> None:
    from app.seed import seed_subscription_plans

    seed_subscription_plans(db_session)
    plans = db_session.scalars(select(SubscriptionPlan)).all()

    assert len(plans) == 4
    student = next(plan for plan in plans if plan.plan_code == "student")
    assert student.monthly_price_usd == Decimal("5.00")
