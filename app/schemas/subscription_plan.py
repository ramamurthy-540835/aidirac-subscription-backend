from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SubscriptionPlanBase(BaseModel):
    plan_code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1)
    monthly_price_usd: Decimal | None = Field(default=None, ge=Decimal("0"))
    monthly_token_limit: int | None = Field(default=None, ge=0)
    features: list[str] = Field(default_factory=list)
    pricing_label: str | None = Field(default=None, max_length=120)
    is_active: bool = True
    display_order: int = Field(default=0, ge=0)

    @field_validator("plan_code")
    @classmethod
    def normalize_plan_code(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("name", "description")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("pricing_label")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("features")
    @classmethod
    def strip_features(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def require_enterprise_label_for_custom_pricing(self) -> "SubscriptionPlanBase":
        if self.monthly_price_usd is None and not self.pricing_label:
            raise ValueError("pricing_label is required when monthly_price_usd is null")
        return self


class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass


class SubscriptionPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1)
    monthly_price_usd: Decimal | None = Field(default=None, ge=Decimal("0"))
    monthly_token_limit: int | None = Field(default=None, ge=0)
    features: list[str] | None = None
    pricing_label: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("name", "description")
    @classmethod
    def strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("pricing_label")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("features")
    @classmethod
    def strip_features(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return [item.strip() for item in value if item.strip()]


class SubscriptionPlanStatusUpdate(BaseModel):
    is_active: bool


class SubscriptionPlanRead(BaseModel):
    id: int
    plan_code: str
    name: str
    description: str
    monthly_price_usd: Decimal | None
    monthly_token_limit: int | None
    features: list[str]
    pricing_label: str | None
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
