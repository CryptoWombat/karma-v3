"""Karma Platform v3 - FastAPI application."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.core.logging_config import setup_logging
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.request_logging_middleware import RequestLoggingMiddleware
from app.db.session import init_db
from app.api.v1 import auth, users, wallets, stake, referrals, admin, stats, validator, transactions
from app.scheduler import start_emission_scheduler, stop_emission_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, setup logging, start emission scheduler. Shutdown: stop scheduler."""
    setup_logging(get_settings().log_level)
    init_db()
    start_emission_scheduler()
    yield
    stop_emission_scheduler()


app = FastAPI(
    title="Karma Platform API",
    description="Token economy backend for Karma - Telegram Mini App",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(users.router, prefix="/v1/users", tags=["Users"])
app.include_router(wallets.router, prefix="/v1/wallets", tags=["Wallets"])
app.include_router(stake.router, prefix="/v1", tags=["Stake"])
app.include_router(referrals.router, prefix="/v1", tags=["Referrals"])
app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])
app.include_router(auth.router, prefix="/v1", tags=["Auth"])
app.include_router(stats.router, prefix="/v1", tags=["Stats"])
app.include_router(transactions.router, prefix="/v1", tags=["Transactions"])
app.include_router(validator.router, prefix="/v1/validator", tags=["Validator"])

# Telegram Mini App (static)
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/app", StaticFiles(directory=str(static_dir), html=True), name="app")


@app.get("/health")
def health():
    """Health check for load balancers."""
    return {"status": "ok", "version": "3.0.0"}


@app.get("/")
def root():
    """Root redirect to docs."""
    return {"message": "Karma Platform API v3", "docs": "/docs"}
