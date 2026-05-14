"""
Market polling workers.
"""
from __future__ import annotations
from api.core.config import settings
from api.core.logging import log
from api.services import stocks_service, telegram_service

async def poll_stocks(ctx: dict) -> None:
    if not settings.stock_list:
        return
    try:
        prices = await stocks_service.get_prices(settings.stock_list)
        log.info("stocks_polled", count=len(prices))
    except Exception as exc:
        log.error("stocks_poll_error", error=str(exc))

async def poll_crypto(ctx: dict) -> None:
    if not settings.crypto_list:
        return
    try:
        prices = await stocks_service.get_crypto(settings.crypto_list)
        log.info("crypto_polled", count=len(prices))
    except Exception as exc:
        log.error("crypto_poll_error", error=str(exc))
