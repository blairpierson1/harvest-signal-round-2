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

# Port coordinates for mapping shipping lanes
PORT_COORDINATES: dict[str, tuple[float, float]] = {
    "BRSSZ": (-23.96, -46.33),   # Santos, Brazil
    "USNYC": (40.69, -74.04),    # New York, USA
    "NLRTM": (51.92, 4.48),      # Rotterdam, Netherlands
    "CIABJ": (5.36, -4.01),      # Abidjan, Ivory Coast
    "CAVAN": (49.28, -123.12),   # Vancouver, Canada
    "CNSHA": (31.23, 121.47),    # Shanghai, China
    "IDBLW": (3.78, 98.68),      # Belawan, Indonesia
}

# Primary export routes for each commodity (origin port -> destination port)
SHIPPING_ROUTES: dict[str, dict[str, str]] = {
    "Coffee": {
        "route": "Santos to New York",
        "origin": "Santos,Brazil",
        "origin_port": "BRSSZ",
        "destination": "NewYork,NY",
        "destination_port": "USNYC",
    },
    "Sugar": {
        "route": "Santos to Rotterdam",
        "origin": "Santos,Brazil",
        "origin_port": "BRSSZ",
        "destination": "Rotterdam,Netherlands",
        "destination_port": "NLRTM",
    },
    "Cocoa": {
        "route": "Abidjan to Rotterdam",
        "origin": "Abidjan,IvoryCoast",
        "origin_port": "CIABJ",
        "destination": "Rotterdam,Netherlands",
        "destination_port": "NLRTM",
    },
    "Orange Juice": {
        "route": "Santos to Rotterdam",
        "origin": "Santos,Brazil",
        "origin_port": "BRSSZ",
        "destination": "Rotterdam,Netherlands",
        "destination_port": "NLRTM",
    },
    "Lumber": {
        "route": "Vancouver to Shanghai",
        "origin": "Vancouver,Canada",
        "origin_port": "CAVAN",
        "destination": "Shanghai,China",
        "destination_port": "CNSHA",
    },
    "Palm Oil": {
        "route": "Belawan to Rotterdam",
        "origin": "Medan,Indonesia",
        "origin_port": "IDBLW",
        "destination": "Rotterdam,Netherlands",
        "destination_port": "NLRTM",
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

        origin_coords = PORT_COORDINATES.get(route_config["origin_port"])
        dest_coords = PORT_COORDINATES.get(route_config["destination_port"])

        return ShippingRate(
            route=route_config["route"],
            origin_port=route_config["origin_port"],
            destination_port=route_config["destination_port"],
            origin_lat=origin_coords[0] if origin_coords else None,
            origin_lon=origin_coords[1] if origin_coords else None,
            destination_lat=dest_coords[0] if dest_coords else None,
            destination_lon=dest_coords[1] if dest_coords else None,
            rate_usd=rate_usd,
            container_type="40ft",
            source="freightos",
        )

    except Exception:
        logger.exception("Failed to fetch shipping rate for %s", commodity)
        origin_coords = PORT_COORDINATES.get(route_config["origin_port"])
        dest_coords = PORT_COORDINATES.get(route_config["destination_port"])

        return ShippingRate(
            route=route_config["route"],
            origin_port=route_config["origin_port"],
            destination_port=route_config["destination_port"],
            origin_lat=origin_coords[0] if origin_coords else None,
            origin_lon=origin_coords[1] if origin_coords else None,
            destination_lat=dest_coords[0] if dest_coords else None,
            destination_lon=dest_coords[1] if dest_coords else None,
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
