from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.token_usage import TokenUsage


class TokenUsageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_event_id(self, event_id: str) -> TokenUsage | None:
        statement = select(TokenUsage).where(TokenUsage.event_id == event_id)
        return self.db.scalar(statement)

    def sum_for_subscription_period(
        self,
        subscription_id: int,
        period_start: datetime,
        period_end: datetime,
    ) -> int:
        statement = select(func.coalesce(func.sum(TokenUsage.total_tokens), 0)).where(
            TokenUsage.subscription_id == subscription_id,
            TokenUsage.usage_period_start == period_start,
            TokenUsage.usage_period_end == period_end,
        )
        return int(self.db.scalar(statement) or 0)

    def list_for_user(self, user_id: str) -> list[TokenUsage]:
        statement = (
            select(TokenUsage)
            .where(TokenUsage.user_id == user_id)
            .order_by(TokenUsage.created_at.desc(), TokenUsage.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def create(self, usage: TokenUsage) -> TokenUsage:
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        return usage
