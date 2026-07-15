from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import SubscriptionPlan
from app.seed import seed_subscription_plans


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_subscription_plans(db)
    yield


settings = get_settings()

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router)
