from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.schemas.subscription_plan import SubscriptionPlanUpdate


def subscribe(client: TestClient, user_id: str = "user-002", plan_code: str = "plus"):
    return client.post(
        "/api/user-subscriptions",
        json={"user_id": user_id, "plan_code": plan_code, "billing_cycle": "monthly"},
    )


def consume(
    client: TestClient,
    event_id: str = "request-001",
    user_id: str = "user-002",
    prompt_tokens: int = 800,
    completion_tokens: int = 200,
):
    return client.post(
        "/api/token-usage/consume",
        json={
            "event_id": event_id,
            "user_id": user_id,
            "request_type": "chat",
            "model_name": "test-model",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": 1,
            "metadata": {"workspace_id": "workspace-001"},
        },
    )


def set_plan_token_limit(db_session: Session, plan_code: str, token_limit: int) -> None:
    repository = SubscriptionPlanRepository(db_session)
    plan = repository.get_by_plan_code(plan_code)
    assert plan is not None
    repository.update(plan, SubscriptionPlanUpdate(monthly_token_limit=token_limit))


def test_valid_usage(client: TestClient) -> None:
    subscription_response = subscribe(client)
    assert subscription_response.status_code == 201

    response = consume(client)

    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == "request-001"
    assert data["subscription_id"] == subscription_response.json()["id"]
    assert data["prompt_tokens"] == 800
    assert data["completion_tokens"] == 200
    assert data["total_tokens"] == 1000
    assert data["metadata"] == {"workspace_id": "workspace-001"}


def test_duplicate_event_id(client: TestClient) -> None:
    assert subscribe(client).status_code == 201
    assert consume(client).status_code == 201

    response = consume(client)

    assert response.status_code == 409
    assert response.json()["detail"] == "Token usage event already exists"


def test_no_active_subscription(client: TestClient) -> None:
    response = consume(client)

    assert response.status_code == 403
    assert response.json()["detail"] == "User has no active subscription"


def test_cancelled_subscription(client: TestClient) -> None:
    assert subscribe(client).status_code == 201
    cancel_response = client.patch("/api/user-subscriptions/user-002/cancel")
    assert cancel_response.status_code == 200

    response = consume(client)

    assert response.status_code == 403
    assert response.json()["detail"] == "User has no active subscription"


def test_exact_quota_boundary(client: TestClient, db_session: Session) -> None:
    set_plan_token_limit(db_session, "plus", 1000)
    assert subscribe(client).status_code == 201

    response = consume(client, prompt_tokens=600, completion_tokens=400)

    assert response.status_code == 201
    assert response.json()["total_tokens"] == 1000


def test_quota_exceeded(client: TestClient, db_session: Session) -> None:
    set_plan_token_limit(db_session, "plus", 999)
    assert subscribe(client).status_code == 201

    response = consume(client, prompt_tokens=600, completion_tokens=400)

    assert response.status_code == 402
    assert response.json()["detail"] == "Token quota exceeded"


def test_enterprise_unlimited_usage(client: TestClient, db_session: Session) -> None:
    assert subscribe(client, user_id="enterprise-user", plan_code="plus").status_code == 201
    from app.repositories.user_subscription_repository import UserSubscriptionRepository

    repository = UserSubscriptionRepository(db_session)
    subscription = repository.get_active_by_user_id("enterprise-user")
    assert subscription is not None
    subscription.plan_code = "enterprise"
    subscription.token_allowance_snapshot = None
    repository.update(subscription)

    response = consume(client, user_id="enterprise-user", prompt_tokens=5_000_000, completion_tokens=5_000_000)

    assert response.status_code == 201
    assert response.json()["total_tokens"] == 10_000_000


def test_usage_summary(client: TestClient, db_session: Session) -> None:
    set_plan_token_limit(db_session, "plus", 2000)
    assert subscribe(client).status_code == 201
    assert consume(client, event_id="request-001", prompt_tokens=800, completion_tokens=200).status_code == 201
    assert consume(client, event_id="request-002", prompt_tokens=250, completion_tokens=250).status_code == 201

    response = client.get("/api/token-usage/user-002/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user-002"
    assert data["plan_code"] == "plus"
    assert data["token_limit"] == 2000
    assert data["tokens_used"] == 1500
    assert data["tokens_remaining"] == 500
    assert data["usage_percent"] == 75.0
    assert data["unlimited"] is False
    assert data["period_start"] < data["period_end"]


def test_usage_event_listing(client: TestClient) -> None:
    assert subscribe(client).status_code == 201
    assert consume(client, event_id="request-001").status_code == 201
    assert consume(client, event_id="request-002", prompt_tokens=100, completion_tokens=50).status_code == 201

    response = client.get("/api/token-usage/user-002/events")

    assert response.status_code == 200
    events = response.json()
    assert [event["event_id"] for event in events] == ["request-002", "request-001"]
    assert events[1]["total_tokens"] == 1000


def test_quota_check(client: TestClient, db_session: Session) -> None:
    set_plan_token_limit(db_session, "plus", 2000)
    assert subscribe(client).status_code == 201
    assert consume(client, prompt_tokens=600, completion_tokens=400).status_code == 201

    allowed_response = client.get("/api/token-usage/user-002/quota-check?requested_tokens=1000")
    denied_response = client.get("/api/token-usage/user-002/quota-check?requested_tokens=1001")

    assert allowed_response.status_code == 200
    assert allowed_response.json()["allowed"] is True
    assert allowed_response.json()["tokens_remaining"] == 1000
    assert denied_response.status_code == 200
    assert denied_response.json()["allowed"] is False
