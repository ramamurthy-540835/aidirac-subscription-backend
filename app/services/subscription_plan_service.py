from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.schemas.subscription_plan import (
    SubscriptionPlanCreate,
    SubscriptionPlanStatusUpdate,
    SubscriptionPlanUpdate,
)


class SubscriptionPlanService:
    def __init__(self, repository: SubscriptionPlanRepository) -> None:
        self.repository = repository

    def list_plans(self, active_only: bool = False):
        return self.repository.list(active_only=active_only)

    def get_plan(self, plan_code: str):
        plan = self.repository.get_by_plan_code(plan_code)
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
        return plan

    def create_plan(self, payload: SubscriptionPlanCreate):
        try:
            return self.repository.create(payload)
        except IntegrityError as exc:
            self.repository.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Subscription plan with this plan_code already exists",
            ) from exc

    def update_plan(self, plan_code: str, payload: SubscriptionPlanUpdate):
        plan = self.get_plan(plan_code)
        return self.repository.update(plan, payload)

    def update_status(self, plan_code: str, payload: SubscriptionPlanStatusUpdate):
        plan = self.get_plan(plan_code)
        return self.repository.update_status(plan, payload.is_active)
