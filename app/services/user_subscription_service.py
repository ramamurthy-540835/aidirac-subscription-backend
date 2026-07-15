from calendar import monthrange
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.models.user_subscription import UserSubscription
from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.repositories.user_subscription_repository import UserSubscriptionRepository
from app.schemas.user_subscription import UserSubscriptionChangePlan, UserSubscriptionCreate


LOCAL_ACTIVE_PLAN_CODES = {"student", "plus", "pro"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def add_months(value: datetime, months: int) -> datetime:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class UserSubscriptionService:
    def __init__(
        self,
        subscription_repository: UserSubscriptionRepository,
        plan_repository: SubscriptionPlanRepository,
    ) -> None:
        self.subscription_repository = subscription_repository
        self.plan_repository = plan_repository

    def create_subscription(self, payload: UserSubscriptionCreate) -> UserSubscription:
        self._ensure_no_current_subscription(payload.user_id)
        plan = self._get_active_plan(payload.plan_code)
        now = utc_now()
        status_value = self._initial_status(plan.plan_code)
        subscription = UserSubscription(
            user_id=payload.user_id,
            plan_code=plan.plan_code,
            status=status_value,
            billing_cycle=payload.billing_cycle.value,
            token_allowance_snapshot=plan.monthly_token_limit,
            started_at=now,
            current_period_start=now,
            current_period_end=self._period_end(now, payload.billing_cycle.value),
        )
        return self.subscription_repository.create(subscription)

    def get_subscription(self, user_id: str) -> UserSubscription:
        subscription = self.subscription_repository.get_latest_by_user_id(user_id)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User subscription not found")
        return subscription

    def cancel_subscription(self, user_id: str) -> UserSubscription:
        subscription = self.subscription_repository.get_current_by_user_id(user_id)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current user subscription not found")
        subscription.status = "cancelled"
        subscription.cancelled_at = utc_now()
        return self.subscription_repository.update(subscription)

    def change_plan(self, user_id: str, payload: UserSubscriptionChangePlan) -> UserSubscription:
        subscription = self.subscription_repository.get_current_by_user_id(user_id)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current user subscription not found")
        plan = self._get_active_plan(payload.plan_code)
        now = utc_now()
        billing_cycle = payload.billing_cycle.value if payload.billing_cycle is not None else subscription.billing_cycle
        subscription.plan_code = plan.plan_code
        subscription.status = self._initial_status(plan.plan_code)
        subscription.billing_cycle = billing_cycle
        subscription.token_allowance_snapshot = plan.monthly_token_limit
        subscription.started_at = now
        subscription.current_period_start = now
        subscription.current_period_end = self._period_end(now, billing_cycle)
        subscription.cancelled_at = None
        return self.subscription_repository.update(subscription)

    def _ensure_no_current_subscription(self, user_id: str) -> None:
        if self.subscription_repository.get_current_by_user_id(user_id) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has a current active or pending subscription",
            )

    def _get_active_plan(self, plan_code: str):
        plan = self.plan_repository.get_by_plan_code(plan_code)
        if plan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
        if not plan.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription plan is inactive")
        return plan

    def _initial_status(self, plan_code: str) -> str:
        if plan_code == "enterprise":
            return "pending"
        if plan_code in LOCAL_ACTIVE_PLAN_CODES:
            return "active"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan cannot be activated without payment-provider integration",
        )

    def _period_end(self, started_at: datetime, billing_cycle: str) -> datetime:
        if billing_cycle == "monthly":
            return add_months(started_at, 1)
        return add_months(started_at, 12)
