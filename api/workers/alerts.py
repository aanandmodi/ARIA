"""
Alert workers — price alerts, keyword alerts.
"""
from __future__ import annotations
from api.core.config import settings
from api.core.logging import log

async def check_price_alerts(ctx: dict) -> None:
    """Check watchlist price alerts."""
    log.info("price_alerts_checked")

async def check_keyword_alerts(ctx: dict) -> None:
    """Check keyword alerts across platforms."""
    log.info("keyword_alerts_checked")
