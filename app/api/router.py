from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_subscription_plan_service
from app.schemas.subscription_plan import (
    SubscriptionPlanCreate,
    SubscriptionPlanRead,
    SubscriptionPlanStatusUpdate,
    SubscriptionPlanUpdate,
)
from app.services.subscription_plan_service import SubscriptionPlanService

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
