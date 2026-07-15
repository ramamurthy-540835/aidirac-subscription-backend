from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription_plan import SubscriptionPlan
from app.schemas.subscription_plan import SubscriptionPlanCreate, SubscriptionPlanUpdate


class SubscriptionPlanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, active_only: bool = False) -> list[SubscriptionPlan]:
        statement = select(SubscriptionPlan)
        if active_only:
            statement = statement.where(SubscriptionPlan.is_active.is_(True))
        statement = statement.order_by(SubscriptionPlan.display_order, SubscriptionPlan.id)
        return list(self.db.scalars(statement).all())

    def get_by_plan_code(self, plan_code: str) -> SubscriptionPlan | None:
        statement = select(SubscriptionPlan).where(SubscriptionPlan.plan_code == plan_code.lower())
        return self.db.scalar(statement)

    def create(self, payload: SubscriptionPlanCreate) -> SubscriptionPlan:
        plan = SubscriptionPlan(**payload.model_dump())
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def update(self, plan: SubscriptionPlan, payload: SubscriptionPlanUpdate) -> SubscriptionPlan:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(plan, field, value)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def update_status(self, plan: SubscriptionPlan, is_active: bool) -> SubscriptionPlan:
        plan.is_active = is_active
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def upsert_seed(self, payload: dict) -> SubscriptionPlan:
        plan = self.get_by_plan_code(payload["plan_code"])
        if plan is None:
            plan = SubscriptionPlan(**payload)
            self.db.add(plan)
        else:
            for field, value in payload.items():
                setattr(plan, field, value)
        self.db.commit()
        self.db.refresh(plan)
        return plan
