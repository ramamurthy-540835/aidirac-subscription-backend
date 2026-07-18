from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.repositories.bigquery_repositories import (
    BigQuerySubscriptionPlanRepository,
    BigQueryTokenUsageRepository,
    BigQueryUserSubscriptionRepository,
)
from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.repositories.token_usage_repository import TokenUsageRepository
from app.repositories.user_subscription_repository import UserSubscriptionRepository
from app.services.subscription_plan_service import SubscriptionPlanService
from app.services.token_usage_service import TokenUsageService
from app.services.user_subscription_service import UserSubscriptionService


def get_subscription_plan_service(db: Session = Depends(get_db)) -> SubscriptionPlanService:
    if get_settings().database_backend == "bigquery":
        return SubscriptionPlanService(BigQuerySubscriptionPlanRepository())
    return SubscriptionPlanService(SubscriptionPlanRepository(db))


def get_user_subscription_service(db: Session = Depends(get_db)) -> UserSubscriptionService:
    if get_settings().database_backend == "bigquery":
        return UserSubscriptionService(
            BigQueryUserSubscriptionRepository(),
            BigQuerySubscriptionPlanRepository(),
        )
    return UserSubscriptionService(
        UserSubscriptionRepository(db),
        SubscriptionPlanRepository(db),
    )


def get_token_usage_service(db: Session = Depends(get_db)) -> TokenUsageService:
    if get_settings().database_backend == "bigquery":
        return TokenUsageService(
            BigQueryTokenUsageRepository(),
            BigQueryUserSubscriptionRepository(),
        )
    return TokenUsageService(
        TokenUsageRepository(db),
        UserSubscriptionRepository(db),
    )
