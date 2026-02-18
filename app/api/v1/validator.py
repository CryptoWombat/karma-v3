"""Validator API - authenticated read-only endpoints for external validators."""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from app.core.dependencies import DbSession, require_validator
from app.services.validator_service import (
    get_validator_snapshot,
    get_inflation_only,
    get_transactions_only,
    get_leaderboard,
)

router = APIRouter()


@router.get("/health")
def validator_health(db: DbSession):
    """Lightweight health for validator integrations. Auth optional; returns DB status."""
    from app.models.protocol import ProtocolBlock

    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    last_block = db.query(ProtocolBlock).order_by(ProtocolBlock.emitted_at.desc()).first()
    last_protocol_block_at = last_block.emitted_at.isoformat().replace("+00:00", "Z") if last_block and last_block.emitted_at else None
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "status": "operational",
        "database": db_status,
        "last_protocol_block_at": last_protocol_block_at,
        "timestamp": now,
    }


@router.get("/snapshot", dependencies=[Depends(require_validator)])
def validator_snapshot(
    db: DbSession,
    include_top: Literal["10", "25", "50", "100"] = Query("10", alias="include_top"),
):
    """Full platform snapshot: users, balances, transactions, inflation, top wallets."""
    return get_validator_snapshot(db, include_top=int(include_top))


@router.get("/inflation", dependencies=[Depends(require_validator)])
def validator_inflation(db: DbSession):
    """Inflation data only (Karma minted in 1h/24h/7d/30d windows)."""
    return get_inflation_only(db)


@router.get("/leaderboard", dependencies=[Depends(require_validator)])
def validator_leaderboard(
    db: DbSession,
    limit: Literal["10", "25", "50", "100"] = Query("10"),
    sort_by: Literal["balance", "total"] = Query("total"),
):
    """Top wallets by balance or total (balance + staked)."""
    return get_leaderboard(db, limit=int(limit), sort_by=sort_by)


@router.get("/transactions", dependencies=[Depends(require_validator)])
def validator_transactions(db: DbSession):
    """Transaction metrics (count, volume) for 24h/7d/30d."""
    return get_transactions_only(db)
