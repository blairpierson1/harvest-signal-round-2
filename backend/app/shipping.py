"""Shipping rate estimates via Freightos public API.

Uses the Freightos public shipping calculator (no API key required)
to get container freight rate estimates for commodity trade routes.
"""

import asyncio
import logging

import httpx

from app.models import ShippingRate

logger = logging.getLogger(__name__)

FREIGHTOS_BASE_URL = "https://ship.freightos.com/api/shippingCalculator"

# Primary export routes for each commodity (origin port -> destination port)
SHIPPING_ROUTES: dict[str, dict[str, str]] = {
    "Pistachios": {
        "route": "Bandar Abbas to Rotterdam",
        "origin": "BandarAbbas,Iran",
        "origin_port": "IRBND",
        "destination": "Rotterdam,Netherlands",
        "destination_port": "NLRTM",
    },
    "Dates": {
        "route": "Jeddah to Rotterdam",
        "origin": "Jeddah,SaudiArabia",
        "origin_port": "SAJED",
        "destination": "Rotterdam,Netherlands",
        "destination_port": "NLRTM",
    },
    "Saffron": {
        "route": "Bandar Abbas to Dubai",
        "origin": "BandarAbbas,Iran",
        "origin_port": "IRBND",
        "destination": "Dubai,UAE",
        "destination_port": "AEJEA",
    },
    "Cotton": {
        "route": "Mersin to Shanghai",
        "origin": "Mersin,Turkey",
        "origin_port": "TRMER",
        "destination": "Shanghai,China",
        "destination_port": "CNSHA",
    },
    "Hazelnuts": {
        "route": "Trabzon to Rotterdam",
        "origin": "Trabzon,Turkey",
        "origin_port": "TRTRB",
        "destination": "Rotterdam,Netherlands",
        "destination_port": "NLRTM",
    },
    "Olive Oil": {
        "route": "Izmir to New York",
        "origin": "Izmir,Turkey",
        "origin_port": "TRIZM",
        "destination": "NewYork,NY",
        "destination_port": "USNYC",
    },
}


async def _fetch_shipping_rate(commodity: str, route_config: dict[str, str]) -> ShippingRate:
    """Fetch container shipping rate estimate from Freightos public API."""
    try:
        params = {
            "loadtype": "container40",
            "weight": "20000",
            "origin": route_config["origin_port"],
            "quantity": "1",
            "destination": route_config["destination_port"],
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(FREIGHTOS_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        # Parse the Freightos response for price estimate
        rate_usd: float | None = None
        if isinstance(data, dict):
            # The API may return different formats
            price_from = data.get("priceFrom")
            price_to = data.get("priceTo")
            if price_from is not None and price_to is not None:
                rate_usd = round((float(price_from) + float(price_to)) / 2, 2)
            elif price_from is not None:
                rate_usd = round(float(price_from), 2)

        return ShippingRate(
            route=route_config["route"],
            origin_port=route_config["origin_port"],
            destination_port=route_config["destination_port"],
            rate_usd=rate_usd,
            container_type="40ft",
            source="freightos",
        )

    except Exception:
        logger.exception("Failed to fetch shipping rate for %s", commodity)
        return ShippingRate(
            route=route_config["route"],
            origin_port=route_config["origin_port"],
            destination_port=route_config["destination_port"],
            rate_usd=None,
            container_type="40ft",
            source="freightos",
        )


async def fetch_all_shipping() -> dict[str, ShippingRate]:
    """Fetch shipping rates for all commodity routes in parallel."""
    commodities = list(SHIPPING_ROUTES.keys())
    configs = list(SHIPPING_ROUTES.values())

    results = await asyncio.gather(
        *[_fetch_shipping_rate(c, cfg) for c, cfg in zip(commodities, configs)]
    )
    return dict(zip(commodities, results))
