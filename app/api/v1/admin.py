"""Admin endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.audit import log_admin_action
from app.core.dependencies import DbSession, require_admin
from app.schemas.user import CreateEventWalletRequest, UnregisterRequest, UserListResponse
from app.schemas.validator import CreateValidatorKeyRequest, RevokeValidatorKeyRequest
from app.schemas.wallet import MintRequest
from app.services.user_service import list_users, unregister_user_admin, create_event_wallet
from app.services.wallet_service import mint_karma
from app.services.backup_service import export_backup, restore_backup
from app.services.emission_service import run_emission_once
from app.services.validator_key_service import create_validator_key, list_validator_keys, revoke_validator_key

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/mint")
def mint(db: DbSession, req: MintRequest):
    """Mint Karma to user."""
    result = mint_karma(db, req.user_id, req.amount)
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    log_admin_action("mint", {"user_id": req.user_id, "amount": req.amount})
    return {"message": result["message"]}


@router.get("/stats")
def admin_stats(db: DbSession):
    """Full network stats (admin only)."""
    from sqlalchemy import func
    from app.models import User, Wallet, Transaction
    from app.models.transaction import TransactionType

    user_count = db.query(User).filter(User.is_system_wallet == False).count()
    total_minted = (
        db.query(func.coalesce(func.sum(Transaction.amount_karma), 0))
        .filter(Transaction.type == TransactionType.MINT)
        .scalar()
        or 0
    )
    total_transferred = (
        db.query(func.coalesce(func.sum(Transaction.amount_karma), 0))
        .filter(Transaction.type == TransactionType.SEND)
        .scalar()
        or 0
    )
    tx_count = db.query(Transaction).filter(Transaction.type == TransactionType.SEND).count()

    total_karma = (
        db.query(func.coalesce(func.sum(Wallet.karma_balance), 0)).scalar() or 0
    )
    total_chiliz = (
        db.query(func.coalesce(func.sum(Wallet.chiliz_balance), 0)).scalar() or 0
    )
    total_staked = (
        db.query(func.coalesce(func.sum(Wallet.staked_amount), 0)).scalar() or 0
    )
    total_rewards = (
        db.query(func.coalesce(func.sum(Wallet.rewards_earned), 0)).scalar() or 0
    )

    return {
        "total_users": user_count,
        "total_minted": float(total_minted),
        "total_transferred": float(total_transferred),
        "total_transactions": tx_count,
        "total_karma_supply": float(total_karma),
        "total_chiliz_supply": float(total_chiliz),
        "total_savings": float(total_staked),
        "total_rewards_earned": float(total_rewards),
    }


@router.get("/users", response_model=UserListResponse)
def admin_list_users(db: DbSession, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    """List users (paginated)."""
    users, total = list_users(db, limit=limit, offset=offset)
    return UserListResponse(users=users, total=total, limit=limit, offset=offset)


@router.post("/event-wallets")
def admin_create_event_wallet(db: DbSession, req: CreateEventWalletRequest):
    """Create an event wallet (special user type for distributions)."""
    result = create_event_wallet(db, req.name)
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    log_admin_action("create_event_wallet", {"name": req.name, "user_id": result.get("user_id")})
    return result


@router.post("/validator-keys")
def admin_create_validator_key(db: DbSession, req: CreateValidatorKeyRequest):
    """Create validator API key. Returns plaintext once - save it securely."""
    result = create_validator_key(db, req.name)
    log_admin_action("create_validator_key", {"name": req.name, "key_id": result.get("key_id")})
    return result


@router.get("/validator-keys")
def admin_list_validator_keys(db: DbSession):
    """List validator keys (without plaintext)."""
    return {"keys": list_validator_keys(db)}


@router.post("/validator-keys/revoke")
def admin_revoke_validator_key(db: DbSession, req: RevokeValidatorKeyRequest):
    """Revoke a validator key."""
    result = revoke_validator_key(db, req.key_id)
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    log_admin_action("revoke_validator_key", {"key_id": str(req.key_id)})
    return result


@router.get("/backup")
def admin_backup(db: DbSession):
    """Export full DB state as JSON backup."""
    return export_backup(db)


@router.post("/restore")
def admin_restore(db: DbSession, data: dict):
    """Restore from backup JSON. Replaces all data."""
    result = restore_backup(db, data)
    log_admin_action("restore", {"users_restored": result.get("users", 0)})
    return result


@router.post("/protocol/run-once")
def admin_protocol_run_once(db: DbSession):
    """Run protocol emission once (manual trigger)."""
    result = run_emission_once(db)
    log_admin_action("protocol_run_once", {"block_id": result.get("block_id"), "reward_total": result.get("reward_total")})
    return result


@router.post("/unregister")
def admin_unregister(db: DbSession, req: UnregisterRequest):
    """Unregister (delete) a user. Cascades to wallet and referrals."""
    result = unregister_user_admin(db, int(req.user_id))
    if "error" in result:
        raise HTTPException(
            status_code=result.get("status", 400),
            detail=result["error"],
        )
    log_admin_action("unregister", {"user_id": req.user_id})
    return result
