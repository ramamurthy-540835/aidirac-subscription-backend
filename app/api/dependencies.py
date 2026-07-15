from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.services.subscription_plan_service import SubscriptionPlanService


def get_subscription_plan_service(db: Session = Depends(get_db)) -> SubscriptionPlanService:
    return SubscriptionPlanService(SubscriptionPlanRepository(db))
