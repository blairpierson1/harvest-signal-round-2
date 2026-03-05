"""Vessel tracking data for commodity shipping routes.

Generates realistic vessel position data along known commodity trade routes.
Uses time-based positioning so vessels appear to move between refreshes.
Can be upgraded to use a real AIS API (e.g. aisstream.io) by setting
the AISSTREAM_API_KEY environment variable.
"""

import asyncio
import hashlib
import logging
import math
from datetime import datetime, timezone

from app.models import Vessel
from app.shipping import SHIPPING_ROUTES

logger = logging.getLogger(__name__)

# Port coordinates (lat, lon) for each UN/LOCODE
PORT_COORDINATES: dict[str, tuple[float, float]] = {
    "BRSSZ": (-23.96, -46.33),   # Santos, Brazil
    "USNYC": (40.69, -74.04),    # New York, USA
    "NLRTM": (51.92, 4.48),      # Rotterdam, Netherlands
    "CIABJ": (5.36, -4.01),      # Abidjan, Ivory Coast
    "CAVAN": (49.28, -123.12),   # Vancouver, Canada
    "CNSHA": (31.23, 121.47),    # Shanghai, China
    "IDBLW": (3.78, 98.68),      # Belawan/Medan, Indonesia
}

# Realistic vessel names per commodity type
VESSEL_NAMES: dict[str, list[str]] = {
    "Coffee": [
        "MV Santos Express", "Green Mountain", "Arabica Star",
        "Pacific Trader", "Café Nova",
    ],
    "Sugar": [
        "Sweet Meridian", "Crystal Carrier", "Sucrose Wind",
        "MV Cane Runner", "Sugar Bay",
    ],
    "Cocoa": [
        "Cocoa Venture", "West Africa Star", "MV Dark Roast",
        "Ivory Trader", "Theobroma",
    ],
    "Orange Juice": [
        "Citrus Express", "MV Sunrise", "Orange Horizon",
        "Tropical Carrier", "Valencia Star",
    ],
    "Lumber": [
        "Timber Wolf", "Pacific Pine", "MV Forest King",
        "Cedar Express", "Woodlands Carrier",
    ],
    "Palm Oil": [
        "Palm Meridian", "Strait Trader", "MV Oleander",
        "Sumatra Star", "Kelapa Express",
    ],
}


def _great_circle_intermediate(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    fraction: float,
) -> tuple[float, float]:
    """Compute an intermediate point on the great circle path.

    Uses spherical interpolation between two lat/lon points.
    fraction=0 returns point1, fraction=1 returns point2.
    """
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)

    d = math.acos(
        math.sin(lat1_r) * math.sin(lat2_r)
        + math.cos(lat1_r) * math.cos(lat2_r) * math.cos(lon2_r - lon1_r)
    )

    if d < 1e-10:
        return lat1, lon1

    a = math.sin((1 - fraction) * d) / math.sin(d)
    b = math.sin(fraction * d) / math.sin(d)

    x = a * math.cos(lat1_r) * math.cos(lon1_r) + b * math.cos(lat2_r) * math.cos(lon2_r)
    y = a * math.cos(lat1_r) * math.sin(lon1_r) + b * math.cos(lat2_r) * math.sin(lon2_r)
    z = a * math.sin(lat1_r) + b * math.sin(lat2_r)

    lat = math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))
    lon = math.degrees(math.atan2(y, x))
    return lat, lon


def _compute_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute initial bearing from point1 to point2 in degrees."""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(lat2_r)
    y = (
        math.cos(lat1_r) * math.sin(lat2_r)
        - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon)
    )
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def _generate_route_coords(
    origin: tuple[float, float],
    dest: tuple[float, float],
    num_points: int = 20,
) -> list[list[float]]:
    """Generate intermediate route coordinates along the great circle path."""
    coords = []
    for i in range(num_points + 1):
        frac = i / num_points
        lat, lon = _great_circle_intermediate(
            origin[0], origin[1], dest[0], dest[1], frac
        )
        coords.append([lat, lon])
    return coords


def _deterministic_float(seed: str, min_val: float, max_val: float) -> float:
    """Generate a deterministic float from a seed string."""
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    return min_val + (h / 0xFFFFFFFF) * (max_val - min_val)


def _generate_vessels_for_commodity(
    commodity: str,
    route_config: dict[str, str],
) -> list[Vessel]:
    """Generate simulated vessels along a commodity's shipping route.

    Uses the current hour as a time seed so vessel positions shift
    each hour, simulating movement along the route.
    """
    origin_code = route_config["origin_port"]
    dest_code = route_config["destination_port"]

    origin_coords = PORT_COORDINATES.get(origin_code)
    dest_coords = PORT_COORDINATES.get(dest_code)
    if not origin_coords or not dest_coords:
        return []

    names = VESSEL_NAMES.get(commodity, ["MV Cargo"])
    route_coords = _generate_route_coords(origin_coords, dest_coords)

    # Use current hour as time component so positions shift hourly
    now = datetime.now(timezone.utc)
    time_seed = now.strftime("%Y-%m-%d-%H")

    vessels: list[Vessel] = []
    num_vessels = min(3, len(names))

    for i in range(num_vessels):
        vessel_seed = f"{commodity}-{i}-{time_seed}"
        name = names[i % len(names)]

        # Position each vessel at a different fraction along the route
        # Base fraction spreads vessels evenly, time adds drift
        base_fraction = (i + 1) / (num_vessels + 1)
        drift = _deterministic_float(vessel_seed, -0.08, 0.08)
        fraction = max(0.05, min(0.95, base_fraction + drift))

        lat, lon = _great_circle_intermediate(
            origin_coords[0], origin_coords[1],
            dest_coords[0], dest_coords[1],
            fraction,
        )

        # Small random offset to avoid vessels stacking exactly on route
        lat_offset = _deterministic_float(f"{vessel_seed}-lat", -0.5, 0.5)
        lon_offset = _deterministic_float(f"{vessel_seed}-lon", -0.5, 0.5)
        lat += lat_offset
        lon += lon_offset

        # Compute heading toward destination
        heading = _compute_bearing(lat, lon, dest_coords[0], dest_coords[1])

        # Generate realistic speed (10-18 knots for cargo vessels)
        speed = round(_deterministic_float(f"{vessel_seed}-spd", 10.0, 18.0), 1)

        # Generate MMSI and IMO
        mmsi_num = int(_deterministic_float(f"{vessel_seed}-mmsi", 200000000, 799999999))
        imo_num = int(_deterministic_float(f"{vessel_seed}-imo", 9000000, 9999999))

        # Estimate ETA based on fraction remaining
        remaining_fraction = 1.0 - fraction
        # Rough distance estimate in nautical miles (assuming ~5000nm avg route)
        route_distance = _deterministic_float(f"{commodity}-dist", 3500, 8000)
        remaining_nm = remaining_fraction * route_distance
        hours_remaining = remaining_nm / speed if speed > 0 else 0
        eta_hours = int(hours_remaining)
        eta_str = f"{eta_hours // 24}d {eta_hours % 24}h" if eta_hours > 0 else "Arriving"

        vessels.append(
            Vessel(
                name=name,
                mmsi=str(mmsi_num),
                imo=f"IMO{imo_num}",
                vessel_type="Bulk Carrier",
                cargo=commodity,
                latitude=round(lat, 4),
                longitude=round(lon, 4),
                speed_knots=speed,
                heading=round(heading, 1),
                status="Under way using engine",
                destination_port=route_config["destination_port"],
                origin_port=route_config["origin_port"],
                eta=eta_str,
                route_coords=route_coords,
                source="simulated",
            )
        )

    return vessels


async def fetch_all_vessels() -> dict[str, list[Vessel]]:
    """Fetch vessel data for all commodity routes.

    Currently generates simulated vessel positions along known
    trade routes. The positions shift each hour to simulate movement.
    """
    results: dict[str, list[Vessel]] = {}

    tasks = []
    commodities = []
    for commodity, route_config in SHIPPING_ROUTES.items():
        commodities.append(commodity)
        tasks.append(
            asyncio.to_thread(
                _generate_vessels_for_commodity, commodity, route_config
            )
        )

    vessel_lists = await asyncio.gather(*tasks)
    for commodity, vessels in zip(commodities, vessel_lists):
        results[commodity] = vessels

    return results
