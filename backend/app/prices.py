"""Price trend data for soft commodities.

All six commodities use Yahoo Finance as the single price source.
No waterfall or fallback to other providers.
"""

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from app.models import PriceHistory, PriceHistoryPoint, PriceTrend

logger = logging.getLogger(__name__)

YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

# Yahoo Finance symbols for tracked commodities.
# Most Middle East commodities lack direct futures tickers on Yahoo Finance;
# only Cotton (CT=F) has a liquid futures contract. Others use estimated prices.
COMMODITY_CONFIG: dict[str, dict[str, str]] = {
    "Pistachios": {},
    "Dates": {},
    "Saffron": {},
    "Cotton": {"symbol": "CT=F"},
    "Hazelnuts": {},
    "Olive Oil": {},
}


async def _fetch_yahoo_price(commodity: str, config: dict[str, str]) -> PriceTrend:
    """Fetch price from Yahoo Finance chart endpoint."""
    try:
        symbol = config["symbol"]
        url = f"{YAHOO_FINANCE_BASE_URL}/{symbol}"
        params = {"range": "5d", "interval": "1d"}
        headers = {"User-Agent": "Mozilla/5.0"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        result = data.get("chart", {}).get("result", [])
        if not result:
            return _get_estimated_price(commodity)

        meta = result[0].get("meta", {})
        current_price = meta.get("regularMarketPrice")
        if current_price is None:
            return _get_estimated_price(commodity)

        prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")

        if prev_close and prev_close > 0:
            change_pct = ((current_price - prev_close) / prev_close) * 100
            direction = (
                "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
            )
        else:
            change_pct = 0.0
            direction = "flat"

        return PriceTrend(
            current_price=round(current_price, 2),
            change_percent=round(change_pct, 2),
            direction=direction,
            source="yahoo_finance",
        )

    except Exception:
        logger.exception("Failed to fetch price from Yahoo Finance for %s", commodity)
        return _get_estimated_price(commodity)


async def fetch_price_trend(commodity: str) -> PriceTrend:
    """Fetch current price trend for a commodity from Yahoo Finance.

    Commodities without a ``symbol`` in COMMODITY_CONFIG fall back to
    estimated prices (most Middle East commodities lack futures tickers).
    """
    config = COMMODITY_CONFIG.get(commodity)
    if not config or "symbol" not in config:
        return _get_estimated_price(commodity)
    return await _fetch_yahoo_price(commodity, config)


def _get_estimated_price(commodity: str) -> PriceTrend:
    """Return estimated commodity prices as fallback when Yahoo Finance fails."""
    estimates: dict[str, PriceTrend] = {
        "Pistachios": PriceTrend(current_price=5.50, change_percent=0.0, direction="flat", source="estimated"),
        "Dates": PriceTrend(current_price=2.50, change_percent=0.0, direction="flat", source="estimated"),
        "Saffron": PriceTrend(current_price=1500.00, change_percent=0.0, direction="flat", source="estimated"),
        "Cotton": PriceTrend(current_price=85.00, change_percent=0.0, direction="flat", source="estimated"),
        "Hazelnuts": PriceTrend(current_price=6.00, change_percent=0.0, direction="flat", source="estimated"),
        "Olive Oil": PriceTrend(current_price=8.50, change_percent=0.0, direction="flat", source="estimated"),
    }
    return estimates.get(commodity, PriceTrend())


async def fetch_all_prices() -> dict[str, PriceTrend]:
    """Fetch price trends for all tracked commodities in parallel."""
    commodities = list(COMMODITY_CONFIG.keys())
    results = await asyncio.gather(
        *[fetch_price_trend(c) for c in commodities]
    )
    return dict(zip(commodities, results))


def _compute_trend_label(points: list[PriceHistoryPoint]) -> str:
    """Determine Uptrend / Downtrend / Sideways from 30-day price history."""
    if len(points) < 5:
        return "N/A"

    first_5_avg = sum(p.close for p in points[:5]) / 5
    last_5_avg = sum(p.close for p in points[-5:]) / 5

    if first_5_avg == 0:
        return "Sideways"

    pct_change = ((last_5_avg - first_5_avg) / first_5_avg) * 100

    if pct_change > 3.0:
        return "Uptrend"
    elif pct_change < -3.0:
        return "Downtrend"
    return "Sideways"


async def fetch_price_history(commodity: str) -> PriceHistory:
    """Fetch 30-day price history from Yahoo Finance for sparkline chart."""
    config = COMMODITY_CONFIG.get(commodity)
    if not config or "symbol" not in config:
        return PriceHistory()

    symbol = config["symbol"]
    try:
        url = f"{YAHOO_FINANCE_BASE_URL}/{symbol}"
        params = {"range": "1mo", "interval": "1d"}
        headers = {"User-Agent": "Mozilla/5.0"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        result = data.get("chart", {}).get("result", [])
        if not result:
            return PriceHistory()

        timestamps = result[0].get("timestamp", [])
        closes_raw = (
            result[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
        )

        points: list[PriceHistoryPoint] = []
        for ts, close in zip(timestamps, closes_raw):
            if close is not None:
                date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                points.append(PriceHistoryPoint(date=date_str, close=round(close, 2)))

        trend_label = _compute_trend_label(points)

        return PriceHistory(
            points=points,
            trend_label=trend_label,
            source="yahoo_finance",
        )

    except Exception:
        logger.exception("Failed to fetch price history for %s", commodity)
        return PriceHistory()


async def fetch_all_price_histories() -> dict[str, PriceHistory]:
    """Fetch 30-day price history for all commodities in parallel."""
    commodities = list(COMMODITY_CONFIG.keys())
    results = await asyncio.gather(
        *[fetch_price_history(c) for c in commodities]
    )
    return dict(zip(commodities, results))
