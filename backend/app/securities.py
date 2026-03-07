"""Investment securities exposure for each tracked commodity.

Provides a static mapping of 1-3 investable securities (ETFs, REITs, stocks,
futures) per commodity so users can act on weather-driven signals.  For
securities with a Yahoo Finance symbol we optionally fetch live price data.
"""

import asyncio
import logging

import httpx

from app.models import InvestmentSecurity

logger = logging.getLogger(__name__)

YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

# ── Static securities config keyed by commodity name ────────────────────────
COMMODITY_SECURITIES: dict[str, list[dict]] = {
    "Pistachios": [
        {
            "ticker": "LAND",
            "name": "Gladstone Land Corp",
            "type": "REIT",
            "description": "US farmland REIT with California pistachio and almond acreage, offering direct exposure to domestic nut production.",
            "yahoo_finance_symbol": "LAND",
        },
        {
            "ticker": "CTVA",
            "name": "Corteva Agriscience",
            "type": "Stock",
            "description": "Crop science company benefiting from rising nut and tree crop demand through seed and crop protection products.",
            "yahoo_finance_symbol": "CTVA",
        },
        {
            "ticker": "FPI",
            "name": "Farmland Partners",
            "type": "REIT",
            "description": "Diversified US farmland REIT with exposure to high-value permanent crops including tree nuts.",
            "yahoo_finance_symbol": "FPI",
        },
    ],
    "Dates": [
        {
            "ticker": "DBA",
            "name": "Invesco DB Agriculture Fund",
            "type": "ETF",
            "description": "Broad agriculture commodity ETF tracking a diversified basket of agricultural futures contracts.",
            "yahoo_finance_symbol": "DBA",
        },
        {
            "ticker": "KSA",
            "name": "iShares MSCI Saudi Arabia ETF",
            "type": "ETF",
            "description": "Saudi Arabia equity ETF providing exposure to the world's second-largest date producing nation.",
            "yahoo_finance_symbol": "KSA",
        },
        {
            "ticker": "UAE",
            "name": "iShares MSCI UAE ETF",
            "type": "ETF",
            "description": "United Arab Emirates equity ETF offering Middle East date production and agricultural trade exposure.",
            "yahoo_finance_symbol": "UAE",
        },
    ],
    "Saffron": [
        {
            "ticker": "DBA",
            "name": "Invesco DB Agriculture Fund",
            "type": "ETF",
            "description": "Broad agriculture commodity ETF; saffron has no direct futures, making DBA the closest liquid proxy.",
            "yahoo_finance_symbol": "DBA",
        },
        {
            "ticker": "MES",
            "name": "Middle East Select ETF",
            "type": "ETF",
            "description": "Middle East equity exposure providing indirect access to Iran-adjacent saffron trade economics.",
            "yahoo_finance_symbol": None,
        },
        {
            "ticker": "REMX",
            "name": "VanEck Rare Earth/Strategic Metals ETF",
            "type": "ETF",
            "description": "Specialty commodity ETF; saffron's rarity and pricing dynamics mirror strategic resource scarcity plays.",
            "yahoo_finance_symbol": "REMX",
        },
    ],
    "Cotton": [
        {
            "ticker": "CT=F",
            "name": "Cotton Futures",
            "type": "Futures",
            "description": "Direct cotton futures contract providing pure-play exposure to cotton price movements.",
            "yahoo_finance_symbol": "CT=F",
        },
        {
            "ticker": "BAL",
            "name": "iPath Series B Bloomberg Cotton Subindex ETN",
            "type": "ETF",
            "description": "Exchange-traded note tracking the Bloomberg Cotton Subindex for direct cotton price exposure without futures accounts.",
            "yahoo_finance_symbol": "BAL",
        },
        {
            "ticker": "DBA",
            "name": "Invesco DB Agriculture Fund",
            "type": "ETF",
            "description": "Diversified agriculture ETF with cotton as a component, offering correlated commodity basket exposure.",
            "yahoo_finance_symbol": "DBA",
        },
    ],
    "Hazelnuts": [
        {
            "ticker": "NSRGY",
            "name": "Nestle SA",
            "type": "Stock",
            "description": "World's largest food company and major hazelnut buyer through its confectionery and spread brands.",
            "yahoo_finance_symbol": "NSRGY",
        },
        {
            "ticker": "MDLZ",
            "name": "Mondelez International",
            "type": "Stock",
            "description": "Global confectionery giant and significant hazelnut consumer through chocolate and snack product lines.",
            "yahoo_finance_symbol": "MDLZ",
        },
        {
            "ticker": "TUR",
            "name": "iShares MSCI Turkey ETF",
            "type": "ETF",
            "description": "Turkey equity ETF providing exposure to the country that produces 70% of the world's hazelnuts.",
            "yahoo_finance_symbol": "TUR",
        },
    ],
    "Olive Oil": [
        {
            "ticker": "EWI",
            "name": "iShares MSCI Italy ETF",
            "type": "ETF",
            "description": "Italy equity ETF offering exposure to a major olive oil producing nation and its agricultural sector.",
            "yahoo_finance_symbol": "EWI",
        },
        {
            "ticker": "EWP",
            "name": "iShares MSCI Spain ETF",
            "type": "ETF",
            "description": "Spain equity ETF providing access to the world's largest olive oil producer by volume.",
            "yahoo_finance_symbol": "EWP",
        },
        {
            "ticker": "DBA",
            "name": "Invesco DB Agriculture Fund",
            "type": "ETF",
            "description": "Broad agriculture commodity ETF serving as the most liquid proxy for olive oil supply-chain dynamics.",
            "yahoo_finance_symbol": "DBA",
        },
    ],
}


async def _fetch_security_price(security: dict) -> InvestmentSecurity:
    """Build an InvestmentSecurity, optionally enriching with live Yahoo Finance price."""
    symbol = security.get("yahoo_finance_symbol")
    current_price: float | None = None
    change_percent: float | None = None

    if symbol:
        try:
            url = f"{YAHOO_FINANCE_BASE_URL}/{symbol}"
            params = {"range": "5d", "interval": "1d"}
            headers = {"User-Agent": "Mozilla/5.0"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

            result = data.get("chart", {}).get("result", [])
            if result:
                meta = result[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                if price is not None:
                    current_price = round(price, 2)
                    prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
                    if prev_close and prev_close > 0:
                        change_percent = round(((price - prev_close) / prev_close) * 100, 2)
        except (httpx.HTTPError, httpx.TimeoutException, KeyError, IndexError, ValueError, TypeError, AttributeError):
            logger.warning("Failed to fetch price for %s, continuing without price data", symbol)

    return InvestmentSecurity(
        ticker=security["ticker"],
        name=security["name"],
        type=security["type"],
        description=security["description"],
        yahoo_finance_symbol=symbol,
        current_price=current_price,
        change_percent=change_percent,
    )


async def fetch_all_securities() -> dict[str, list[InvestmentSecurity]]:
    """Return investment securities for all commodities, with optional live prices."""
    all_tasks: list[tuple[str, dict]] = []
    for commodity, securities in COMMODITY_SECURITIES.items():
        for sec in securities:
            all_tasks.append((commodity, sec))

    results = await asyncio.gather(
        *[_fetch_security_price(sec) for _, sec in all_tasks]
    )

    grouped: dict[str, list[InvestmentSecurity]] = {}
    for (commodity, _), security in zip(all_tasks, results):
        if commodity not in grouped:
            grouped[commodity] = []
        grouped[commodity].append(security)

    return grouped
