from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_subscription import UserSubscription


CURRENT_STATUSES = ("active", "pending")


class UserSubscriptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_current_by_user_id(self, user_id: str) -> UserSubscription | None:
        statement = (
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(CURRENT_STATUSES),
            )
            .order_by(UserSubscription.id.desc())
        )
        return self.db.scalar(statement)

    def get_active_by_user_id(self, user_id: str) -> UserSubscription | None:
        statement = (
            select(UserSubscription)
            .where(
                UserSubscription.user_id == user_id,
                UserSubscription.status == "active",
            )
            .order_by(UserSubscription.id.desc())
        )
        return self.db.scalar(statement)

    def get_latest_by_user_id(self, user_id: str) -> UserSubscription | None:
        statement = (
            select(UserSubscription)
            .where(UserSubscription.user_id == user_id)
            .order_by(UserSubscription.id.desc())
        )
        return self.db.scalar(statement)

    def create(self, subscription: UserSubscription) -> UserSubscription:
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def update(self, subscription: UserSubscription) -> UserSubscription:
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
