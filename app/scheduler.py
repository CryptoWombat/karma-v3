"""Background scheduler for protocol emission."""
import asyncio
import logging

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.emission_service import run_emission_once

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None


async def _run_emission_loop() -> None:
    """Run protocol emission on configured interval."""
    settings = get_settings()
    interval = settings.protocol_interval_seconds
    enabled = getattr(settings, "protocol_scheduled_enabled", True)

    if not enabled or interval <= 0:
        logger.info("Protocol scheduled emission disabled (protocol_scheduled_enabled=false or interval<=0)")
        return

    logger.info("Starting protocol emission scheduler (interval=%ds)", interval)

    while True:
        try:
            db = SessionLocal()
            try:
                result = run_emission_once(db)
                logger.info(
                    "Protocol emission block %s completed (reward=%.2f, processed=%d)",
                    result.get("block_id"),
                    result.get("reward_total", 0),
                    result.get("processed_tx_count", 0),
                )
            except Exception as e:
                logger.exception("Protocol emission failed: %s", e)
            finally:
                db.close()
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Protocol emission scheduler stopped")
            raise
        except Exception as e:
            logger.exception("Emission loop error: %s", e)


def start_emission_scheduler() -> asyncio.Task | None:
    """Start the protocol emission background task."""
    global _task
    if _task is not None:
        return _task
    _task = asyncio.create_task(_run_emission_loop())
    return _task


def stop_emission_scheduler() -> None:
    """Stop the protocol emission background task."""
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
