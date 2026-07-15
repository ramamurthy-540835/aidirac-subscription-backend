import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.api.dependencies import get_subscription_plan_service
from app.api.dependencies import get_token_usage_service
from app.api.dependencies import get_user_subscription_service
from app.api.router import router
from app.db.base import Base
from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.repositories.token_usage_repository import TokenUsageRepository
from app.repositories.user_subscription_repository import UserSubscriptionRepository
from app.seed import seed_subscription_plans
from app.services.subscription_plan_service import SubscriptionPlanService
from app.services.token_usage_service import TokenUsageService
from app.services.user_subscription_service import UserSubscriptionService
from fastapi import FastAPI


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        seed_subscription_plans(db)
        yield db


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    def override_service() -> SubscriptionPlanService:
        return SubscriptionPlanService(SubscriptionPlanRepository(db_session))

    def override_user_subscription_service() -> UserSubscriptionService:
        return UserSubscriptionService(
            UserSubscriptionRepository(db_session),
            SubscriptionPlanRepository(db_session),
        )

    def override_token_usage_service() -> TokenUsageService:
        return TokenUsageService(
            TokenUsageRepository(db_session),
            UserSubscriptionRepository(db_session),
        )

    app.dependency_overrides[get_subscription_plan_service] = override_service
    app.dependency_overrides[get_user_subscription_service] = override_user_subscription_service
    app.dependency_overrides[get_token_usage_service] = override_token_usage_service
    return TestClient(app)
