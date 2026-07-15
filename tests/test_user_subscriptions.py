from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.schemas.subscription_plan import SubscriptionPlanUpdate


def create_subscription(client: TestClient, user_id: str = "user-001", plan_code: str = "plus"):
    return client.post(
        "/api/user-subscriptions",
        json={
            "user_id": user_id,
            "plan_code": plan_code,
            "billing_cycle": "monthly",
        },
    )


def test_create_subscription(client: TestClient) -> None:
    response = create_subscription(client)

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "user-001"
    assert data["plan_code"] == "plus"
    assert data["status"] == "active"
    assert data["billing_cycle"] == "monthly"
    assert data["token_allowance_snapshot"] == 3000000
    assert data["cancelled_at"] is None
    assert data["current_period_start"] < data["current_period_end"]


def test_enterprise_subscription_is_created_pending(client: TestClient) -> None:
    response = create_subscription(client, user_id="enterprise-user", plan_code="enterprise")

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["token_allowance_snapshot"] is None


def test_invalid_plan(client: TestClient) -> None:
    response = create_subscription(client, plan_code="missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Subscription plan not found"


def test_inactive_plan(client: TestClient) -> None:
    status_response = client.patch("/api/subscription-plans/student/status", json={"is_active": False})
    assert status_response.status_code == 200

    response = create_subscription(client, plan_code="student")

    assert response.status_code == 400
    assert response.json()["detail"] == "Subscription plan is inactive"


def test_duplicate_active_subscription(client: TestClient) -> None:
    first_response = create_subscription(client)
    assert first_response.status_code == 201

    duplicate_response = create_subscription(client, plan_code="pro")

    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == "User already has a current active or pending subscription"


def test_reading_subscription(client: TestClient) -> None:
    create_response = create_subscription(client)
    assert create_response.status_code == 201

    response = client.get("/api/user-subscriptions/user-001")

    assert response.status_code == 200
    assert response.json()["id"] == create_response.json()["id"]
    assert response.json()["plan_code"] == "plus"


def test_cancel_subscription(client: TestClient) -> None:
    create_response = create_subscription(client)
    assert create_response.status_code == 201

    response = client.patch("/api/user-subscriptions/user-001/cancel")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["cancelled_at"] is not None


def test_changing_plans(client: TestClient) -> None:
    create_response = create_subscription(client)
    assert create_response.status_code == 201

    response = client.patch(
        "/api/user-subscriptions/user-001/change-plan",
        json={"plan_code": "pro", "billing_cycle": "yearly"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["plan_code"] == "pro"
    assert data["status"] == "active"
    assert data["billing_cycle"] == "yearly"
    assert data["token_allowance_snapshot"] == 15000000


def test_subscription_uses_plan_snapshot_not_client_values(client: TestClient, db_session: Session) -> None:
    repository = SubscriptionPlanRepository(db_session)
    plus = repository.get_by_plan_code("plus")
    assert plus is not None
    repository.update(plus, SubscriptionPlanUpdate(monthly_token_limit=12345))

    response = client.post(
        "/api/user-subscriptions",
        json={
            "user_id": "user-001",
            "plan_code": "plus",
            "billing_cycle": "monthly",
            "token_allowance_snapshot": 999999999,
            "monthly_price_usd": "0.01",
        },
    )

    assert response.status_code == 201
    assert response.json()["token_allowance_snapshot"] == 12345
