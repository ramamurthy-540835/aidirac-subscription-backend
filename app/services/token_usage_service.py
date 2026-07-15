from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.token_usage import TokenUsage
from app.models.user_subscription import UserSubscription
from app.repositories.token_usage_repository import TokenUsageRepository
from app.repositories.user_subscription_repository import UserSubscriptionRepository
from app.schemas.token_usage import QuotaCheck, TokenUsageConsume, TokenUsageSummary


class TokenUsageService:
    def __init__(
        self,
        usage_repository: TokenUsageRepository,
        subscription_repository: UserSubscriptionRepository,
    ) -> None:
        self.usage_repository = usage_repository
        self.subscription_repository = subscription_repository

    def consume(self, payload: TokenUsageConsume) -> TokenUsage:
        if self.usage_repository.get_by_event_id(payload.event_id) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token usage event already exists")

        subscription = self._get_active_subscription(payload.user_id)
        total_tokens = payload.prompt_tokens + payload.completion_tokens
        self._ensure_quota_available(subscription, total_tokens)

        usage = TokenUsage(
            event_id=payload.event_id,
            user_id=payload.user_id,
            subscription_id=subscription.id,
            request_type=payload.request_type,
            model_name=payload.model_name,
            prompt_tokens=payload.prompt_tokens,
            completion_tokens=payload.completion_tokens,
            total_tokens=total_tokens,
            usage_period_start=subscription.current_period_start,
            usage_period_end=subscription.current_period_end,
            metadata_json=payload.metadata,
        )
        try:
            return self.usage_repository.create(usage)
        except IntegrityError as exc:
            self.usage_repository.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token usage event already exists") from exc

    def summary(self, user_id: str) -> TokenUsageSummary:
        subscription = self._get_active_subscription(user_id)
        tokens_used = self._tokens_used(subscription)
        token_limit = subscription.token_allowance_snapshot
        unlimited = token_limit is None
        tokens_remaining = None if unlimited else max(token_limit - tokens_used, 0)
        usage_percent = None if unlimited or token_limit == 0 else round((tokens_used / token_limit) * 100, 2)
        return TokenUsageSummary(
            user_id=user_id,
            plan_code=subscription.plan_code,
            token_limit=token_limit,
            tokens_used=tokens_used,
            tokens_remaining=tokens_remaining,
            usage_percent=usage_percent,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            unlimited=unlimited,
        )

    def list_events(self, user_id: str) -> list[TokenUsage]:
        self._get_active_subscription(user_id)
        return self.usage_repository.list_for_user(user_id)

    def quota_check(self, user_id: str, requested_tokens: int) -> QuotaCheck:
        subscription = self._get_active_subscription(user_id)
        tokens_used = self._tokens_used(subscription)
        token_limit = subscription.token_allowance_snapshot
        unlimited = token_limit is None
        tokens_remaining = None if unlimited else max(token_limit - tokens_used, 0)
        allowed = unlimited or tokens_used + requested_tokens <= token_limit
        return QuotaCheck(
            user_id=user_id,
            requested_tokens=requested_tokens,
            token_limit=token_limit,
            tokens_used=tokens_used,
            tokens_remaining=tokens_remaining,
            allowed=allowed,
            unlimited=unlimited,
        )

    def _get_active_subscription(self, user_id: str) -> UserSubscription:
        subscription = self.subscription_repository.get_active_by_user_id(user_id)
        if subscription is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no active subscription")
        return subscription

    def _ensure_quota_available(self, subscription: UserSubscription, requested_tokens: int) -> None:
        token_limit = subscription.token_allowance_snapshot
        if token_limit is None:
            return
        tokens_used = self._tokens_used(subscription)
        if tokens_used + requested_tokens > token_limit:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Token quota exceeded")

    def _tokens_used(self, subscription: UserSubscription) -> int:
        return self.usage_repository.sum_for_subscription_period(
            subscription.id,
            subscription.current_period_start,
            subscription.current_period_end,
        )
