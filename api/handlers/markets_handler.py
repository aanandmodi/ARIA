"""
Markets handler — get stock and crypto prices.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from api.services import telegram_service, stocks_service

async def handle(params: dict, db: AsyncSession, update: Update) -> None:
    """Handle markets intent."""
    symbols = params.get("symbols", [])
    
    await telegram_service.send_typing()
    
    if not symbols:
        # Default symbols if none specified
        stocks = await stocks_service.get_prices(["AAPL", "MSFT", "GOOGL"])
        crypto = await stocks_service.get_crypto(["bitcoin", "ethereum"])
    else:
        # Try fetching everything as both stock and crypto to see what hits
        stocks = await stocks_service.get_prices(symbols)
        
        # Coingecko uses full lowercase names mostly, but we'll try whatever we have
        crypto_ids = [s.lower() for s in symbols]
        crypto = await stocks_service.get_crypto(crypto_ids)

    response = stocks_service.format_prices(stocks, crypto)
    await telegram_service.send_message(f"📊 <b>Markets</b>\n\n{response}")
