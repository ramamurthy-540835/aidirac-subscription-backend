from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.repositories.token_usage_repository import TokenUsageRepository
from app.repositories.user_subscription_repository import UserSubscriptionRepository
from app.services.subscription_plan_service import SubscriptionPlanService
from app.services.token_usage_service import TokenUsageService
from app.services.user_subscription_service import UserSubscriptionService


def get_subscription_plan_service(db: Session = Depends(get_db)) -> SubscriptionPlanService:
    return SubscriptionPlanService(SubscriptionPlanRepository(db))


def get_user_subscription_service(db: Session = Depends(get_db)) -> UserSubscriptionService:
    return UserSubscriptionService(
        UserSubscriptionRepository(db),
        SubscriptionPlanRepository(db),
    )


def get_token_usage_service(db: Session = Depends(get_db)) -> TokenUsageService:
    return TokenUsageService(
        TokenUsageRepository(db),
        UserSubscriptionRepository(db),
    )
