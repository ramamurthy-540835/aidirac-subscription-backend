from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    get_subscription_plan_service,
    get_token_usage_service,
    get_user_subscription_service,
)
from app.schemas.subscription_plan import (
    SubscriptionPlanCreate,
    SubscriptionPlanRead,
    SubscriptionPlanStatusUpdate,
    SubscriptionPlanUpdate,
)
from app.schemas.token_usage import QuotaCheck, TokenUsageConsume, TokenUsageRead, TokenUsageSummary
from app.schemas.user_subscription import (
    UserSubscriptionChangePlan,
    UserSubscriptionCreate,
    UserSubscriptionRead,
)
from app.services.subscription_plan_service import SubscriptionPlanService
from app.services.token_usage_service import TokenUsageService
from app.services.user_subscription_service import UserSubscriptionService

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/subscription-plans", response_model=list[SubscriptionPlanRead])
def list_subscription_plans(
    active_only: bool = Query(default=False),
    service: SubscriptionPlanService = Depends(get_subscription_plan_service),
):
    return service.list_plans(active_only=active_only)


@router.get("/subscription-plans/{plan_code}", response_model=SubscriptionPlanRead)
def get_subscription_plan(
    plan_code: str,
    service: SubscriptionPlanService = Depends(get_subscription_plan_service),
):
    return service.get_plan(plan_code)


@router.post("/subscription-plans", response_model=SubscriptionPlanRead, status_code=status.HTTP_201_CREATED)
def create_subscription_plan(
    payload: SubscriptionPlanCreate,
    service: SubscriptionPlanService = Depends(get_subscription_plan_service),
):
    return service.create_plan(payload)


@router.put("/subscription-plans/{plan_code}", response_model=SubscriptionPlanRead)
def update_subscription_plan(
    plan_code: str,
    payload: SubscriptionPlanUpdate,
    service: SubscriptionPlanService = Depends(get_subscription_plan_service),
):
    return service.update_plan(plan_code, payload)


@router.patch("/subscription-plans/{plan_code}/status", response_model=SubscriptionPlanRead)
def update_subscription_plan_status(
    plan_code: str,
    payload: SubscriptionPlanStatusUpdate,
    service: SubscriptionPlanService = Depends(get_subscription_plan_service),
):
    return service.update_status(plan_code, payload)


@router.post("/user-subscriptions", response_model=UserSubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_user_subscription(
    payload: UserSubscriptionCreate,
    service: UserSubscriptionService = Depends(get_user_subscription_service),
):
    return service.create_subscription(payload)


@router.get("/user-subscriptions/{user_id}", response_model=UserSubscriptionRead)
def get_user_subscription(
    user_id: str,
    service: UserSubscriptionService = Depends(get_user_subscription_service),
):
    return service.get_subscription(user_id)


@router.patch("/user-subscriptions/{user_id}/cancel", response_model=UserSubscriptionRead)
def cancel_user_subscription(
    user_id: str,
    service: UserSubscriptionService = Depends(get_user_subscription_service),
):
    return service.cancel_subscription(user_id)


@router.patch("/user-subscriptions/{user_id}/change-plan", response_model=UserSubscriptionRead)
def change_user_subscription_plan(
    user_id: str,
    payload: UserSubscriptionChangePlan,
    service: UserSubscriptionService = Depends(get_user_subscription_service),
):
    return service.change_plan(user_id, payload)


@router.post("/token-usage/consume", response_model=TokenUsageRead, status_code=status.HTTP_201_CREATED)
def consume_token_usage(
    payload: TokenUsageConsume,
    service: TokenUsageService = Depends(get_token_usage_service),
):
    return service.consume(payload)


@router.get("/token-usage/{user_id}/summary", response_model=TokenUsageSummary)
def get_token_usage_summary(
    user_id: str,
    service: TokenUsageService = Depends(get_token_usage_service),
):
    return service.summary(user_id)


@router.get("/token-usage/{user_id}/events", response_model=list[TokenUsageRead])
def list_token_usage_events(
    user_id: str,
    service: TokenUsageService = Depends(get_token_usage_service),
):
    return service.list_events(user_id)


@router.get("/token-usage/{user_id}/quota-check", response_model=QuotaCheck)
def check_token_quota(
    user_id: str,
    requested_tokens: int = Query(..., ge=0),
    service: TokenUsageService = Depends(get_token_usage_service),
):
    return service.quota_check(user_id, requested_tokens)
