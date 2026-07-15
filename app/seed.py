from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.subscription_plan_repository import SubscriptionPlanRepository


INITIAL_SUBSCRIPTION_PLANS = [
    {
        "plan_code": "student",
        "name": "Student",
        "description": "Affordable access for students learning and building with AIDIRAC.",
        "monthly_price_usd": Decimal("5.00"),
        "monthly_token_limit": 500000,
        "features": ["Core AIDIRAC access", "Student token allowance", "Community support"],
        "pricing_label": None,
        "is_active": True,
        "display_order": 1,
    },
    {
        "plan_code": "plus",
        "name": "Plus",
        "description": "Expanded monthly capacity for individual creators and builders.",
        "monthly_price_usd": Decimal("20.00"),
        "monthly_token_limit": 3000000,
        "features": ["Higher token allowance", "Standard model access", "Email support"],
        "pricing_label": None,
        "is_active": True,
        "display_order": 2,
    },
    {
        "plan_code": "pro",
        "name": "Pro",
        "description": "Professional capacity for advanced workflows and production usage.",
        "monthly_price_usd": Decimal("75.00"),
        "monthly_token_limit": 15000000,
        "features": ["Large token allowance", "Advanced model access", "Priority support"],
        "pricing_label": None,
        "is_active": True,
        "display_order": 3,
    },
    {
        "plan_code": "enterprise",
        "name": "Enterprise",
        "description": "Custom capacity, support, and terms for organizations.",
        "monthly_price_usd": None,
        "monthly_token_limit": None,
        "features": ["Custom token limits", "Dedicated support", "Custom terms"],
        "pricing_label": "Contact Sales",
        "is_active": True,
        "display_order": 4,
    },
]


def seed_subscription_plans(db: Session) -> None:
    repository = SubscriptionPlanRepository(db)
    for plan in INITIAL_SUBSCRIPTION_PLANS:
        repository.upsert_seed(plan)
