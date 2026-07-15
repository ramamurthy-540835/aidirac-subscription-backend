from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class TokenUsageConsume(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=120)
    user_id: str = Field(..., min_length=1, max_length=120)
    request_type: str = Field(..., min_length=1, max_length=64)
    model_name: str = Field(..., min_length=1, max_length=120)
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    metadata: dict = Field(default_factory=dict)

    @field_validator("event_id", "user_id", "request_type", "model_name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class TokenUsageRead(BaseModel):
    id: int
    event_id: str
    user_id: str
    subscription_id: int
    request_type: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    usage_period_start: datetime
    usage_period_end: datetime
    metadata_json: dict
    created_at: datetime

    @computed_field
    @property
    def metadata(self) -> dict:
        return self.metadata_json

    model_config = ConfigDict(from_attributes=True)


class TokenUsageSummary(BaseModel):
    user_id: str
    plan_code: str
    token_limit: int | None
    tokens_used: int
    tokens_remaining: int | None
    usage_percent: float | None
    period_start: datetime
    period_end: datetime
    unlimited: bool


class QuotaCheck(BaseModel):
    user_id: str
    requested_tokens: int
    token_limit: int | None
    tokens_used: int
    tokens_remaining: int | None
    allowed: bool
    unlimited: bool
