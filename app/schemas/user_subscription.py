from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SubscriptionStatus(StrEnum):
    pending = "pending"
    active = "active"
    past_due = "past_due"
    cancelled = "cancelled"
    expired = "expired"


class BillingCycle(StrEnum):
    monthly = "monthly"
    yearly = "yearly"


class UserSubscriptionCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=120)
    plan_code: str = Field(..., min_length=1, max_length=64)
    billing_cycle: BillingCycle

    @field_validator("user_id", "plan_code")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("plan_code")
    @classmethod
    def normalize_plan_code(cls, value: str) -> str:
        return value.lower()


class UserSubscriptionChangePlan(BaseModel):
    plan_code: str = Field(..., min_length=1, max_length=64)
    billing_cycle: BillingCycle | None = None

    @field_validator("plan_code")
    @classmethod
    def normalize_plan_code(cls, value: str) -> str:
        stripped = value.strip().lower()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class UserSubscriptionRead(BaseModel):
    id: int
    user_id: str
    plan_code: str
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    token_allowance_snapshot: int | None
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
