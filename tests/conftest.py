import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.api.dependencies import get_subscription_plan_service
from app.api.router import router
from app.db.base import Base
from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.seed import seed_subscription_plans
from app.services.subscription_plan_service import SubscriptionPlanService
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

    app.dependency_overrides[get_subscription_plan_service] = override_service
    return TestClient(app)
