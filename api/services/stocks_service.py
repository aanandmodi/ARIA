"""
Stocks + crypto service — yfinance + CoinGecko.
"""

from __future__ import annotations

import asyncio
from functools import partial

import httpx
import yfinance as yf

from api.core.logging import log

COINGECKO_API = "https://api.coingecko.com/api/v3"


async def get_prices(tickers: list[str]) -> dict[str, float]:
    """
    Get latest stock prices for given tickers using yfinance.
    Runs in executor since yfinance is synchronous.
    """
    if not tickers:
        return {}
    try:
        loop = asyncio.get_event_loop()

        def _fetch() -> dict[str, float]:
            result = {}
            for ticker in tickers:
                try:
                    t = yf.Ticker(ticker)
                    info = t.fast_info
                    price = getattr(info, "last_price", None)
                    if price is not None:
                        result[ticker] = round(float(price), 2)
                except Exception:
                    continue
            return result

        return await loop.run_in_executor(None, _fetch)
    except Exception as exc:
        log.error("stocks_fetch_failed", error=str(exc))
        return {}


async def get_crypto(coin_ids: list[str]) -> dict[str, float]:
    """
    Get latest crypto prices from CoinGecko (free, no auth).
    """
    if not coin_ids:
        return {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{COINGECKO_API}/simple/price",
                params={
                    "ids": ",".join(coin_ids),
                    "vs_currencies": "usd",
                },
                headers={"User-Agent": "ARIA/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()

        return {
            coin: data[coin]["usd"]
            for coin in data
            if "usd" in data.get(coin, {})
        }
    except Exception as exc:
        log.error("crypto_fetch_failed", error=str(exc))
        return {}


def format_prices(stocks: dict[str, float], crypto: dict[str, float]) -> str:
    """Format market data for briefing."""
    lines: list[str] = []
    if stocks:
        lines.append("📈 Stocks:")
        for ticker, price in stocks.items():
            lines.append(f"  {ticker}: ${price:,.2f}")
    if crypto:
        lines.append("🪙 Crypto:")
        for coin, price in crypto.items():
            lines.append(f"  {coin}: ${price:,.2f}")
    return "\n".join(lines) if lines else "No market data."
