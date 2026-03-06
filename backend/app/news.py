"""News headlines for commodities via NewsAPI.org."""

import asyncio
import logging
import os

import httpx

from app.models import NewsHeadline

logger = logging.getLogger(__name__)

NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"

# Search keywords per commodity
COMMODITY_KEYWORDS: dict[str, str] = {
    "Pistachios": "pistachio commodity price Iran",
    "Dates": "dates commodity Middle East price",
    "Saffron": "saffron commodity price Iran",
    "Cotton": "cotton commodity price Egypt Turkey",
    "Hazelnuts": "hazelnut commodity price Turkey",
    "Olive Oil": "olive oil commodity price Mediterranean",
}


def _get_newsapi_key() -> str | None:
    """Read the NewsAPI key from environment."""
    return os.environ.get("NEWSAPI_KEY")


async def _fetch_commodity_news(commodity: str, keyword: str) -> list[NewsHeadline]:
    """Fetch top 3 recent news headlines for a commodity."""
    api_key = _get_newsapi_key()
    if not api_key:
        logger.warning("NEWSAPI_KEY not set, skipping news for %s", commodity)
        return []

    try:
        params = {
            "q": keyword,
            "sortBy": "publishedAt",
            "pageSize": 3,
            "language": "en",
        }
        headers = {"X-Api-Key": api_key}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(NEWSAPI_BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        articles = data.get("articles", [])
        headlines: list[NewsHeadline] = []
        for article in articles[:3]:
            headlines.append(
                NewsHeadline(
                    title=article.get("title", "No title"),
                    source=article.get("source", {}).get("name", "Unknown"),
                    url=article.get("url", ""),
                    published_at=article.get("publishedAt", ""),
                )
            )
        return headlines

    except (httpx.HTTPError, httpx.TimeoutException, KeyError, ValueError):
        logger.exception("Failed to fetch news for %s", commodity)
        return []


async def fetch_all_news() -> dict[str, list[NewsHeadline]]:
    """Fetch news headlines for all commodities in parallel."""
    commodities = list(COMMODITY_KEYWORDS.keys())
    keywords = list(COMMODITY_KEYWORDS.values())

    results = await asyncio.gather(
        *[_fetch_commodity_news(c, k) for c, k in zip(commodities, keywords)]
    )
    return dict(zip(commodities, results))
