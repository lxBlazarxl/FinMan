from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_current_user
from app.api.v1.auth import router as auth_router
from app.api.v1.household import router as household_router
from app.api.v1.accounts import router as accounts_router
from app.api.v1.balances import router as balances_router
from app.core.config import settings
from app.core.database import engine
from app.models.base import Base


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)

    app.include_router(auth_router, prefix=settings.API_V1_STR)
    app.include_router(household_router, prefix=settings.API_V1_STR)
    app.include_router(accounts_router, prefix=settings.API_V1_STR)
    app.include_router(balances_router, prefix=settings.API_V1_STR)

    @app.get("/health")
    def health() -> dict:
        return {"status": "healthy", "service": "finman"}

    @app.get("/")
    def root() -> dict:
        return {"message": "Welcome to FinMan API", "docs": "/docs"}

    return app


app = create_app()
