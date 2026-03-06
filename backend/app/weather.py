"""Weather data fetching from Open-Meteo API."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

# Growing region coordinates for all five commodities
COMMODITY_REGIONS: dict[str, list[dict]] = {
    "Pistachios": [
        {"region_name": "Kerman Province", "country": "Iran", "latitude": 30.28, "longitude": 57.08},
        {"region_name": "Gaziantep", "country": "Turkey", "latitude": 37.07, "longitude": 37.38},
        {"region_name": "Aleppo Region", "country": "Syria", "latitude": 36.20, "longitude": 37.15},
    ],
    "Figs": [
        {"region_name": "Aydin Province", "country": "Turkey", "latitude": 37.85, "longitude": 27.85},
        {"region_name": "Fars Province", "country": "Iran", "latitude": 29.62, "longitude": 52.53},
        {"region_name": "Bekaa Valley", "country": "Lebanon", "latitude": 33.85, "longitude": 35.90},
    ],
    "Olives": [
        {"region_name": "Aegean Region", "country": "Turkey", "latitude": 38.42, "longitude": 27.14},
        {"region_name": "Northern Israel", "country": "Israel", "latitude": 32.82, "longitude": 35.17},
        {"region_name": "Ajloun", "country": "Jordan", "latitude": 32.33, "longitude": 35.75},
    ],
    "Dates": [
        {"region_name": "Al-Ahsa Oasis", "country": "Saudi Arabia", "latitude": 25.38, "longitude": 49.59},
        {"region_name": "Basra Province", "country": "Iraq", "latitude": 30.51, "longitude": 47.81},
        {"region_name": "Khuzestan Province", "country": "Iran", "latitude": 31.32, "longitude": 48.67},
    ],
    "Citrus": [
        {"region_name": "Mediterranean Coast", "country": "Turkey", "latitude": 36.90, "longitude": 30.70},
        {"region_name": "Coastal Plain", "country": "Israel", "latitude": 32.08, "longitude": 34.78},
        {"region_name": "Bekaa Valley", "country": "Lebanon", "latitude": 33.85, "longitude": 35.90},
    ],
}

# Typical monthly averages for reference (simplified baselines)
BASELINE_TEMP: dict[str, dict[str, float]] = {
    "Pistachios": {"Iran": 28.0, "Turkey": 22.0},
    "Figs": {"Turkey": 24.0, "Iran": 26.0, "Lebanon": 22.0},
    "Olives": {"Turkey": 20.0, "Israel": 24.0, "Jordan": 25.0},
    "Dates": {"Saudi Arabia": 35.0, "Iraq": 33.0, "Iran": 32.0},
    "Citrus": {"Turkey": 20.0, "Israel": 22.0, "Lebanon": 20.0},
}

BASELINE_PRECIP: dict[str, dict[str, float]] = {
    "Pistachios": {"Iran": 0.5, "Turkey": 1.5},
    "Figs": {"Turkey": 1.5, "Iran": 0.8, "Lebanon": 2.0},
    "Olives": {"Turkey": 2.0, "Israel": 1.5, "Jordan": 1.0},
    "Dates": {"Saudi Arabia": 0.2, "Iraq": 0.5, "Iran": 0.5},
    "Citrus": {"Turkey": 2.5, "Israel": 1.5, "Lebanon": 2.5},
}


async def fetch_region_weather(latitude: float, longitude: float) -> dict:
    """Fetch 7-day weather data for a specific coordinate from Open-Meteo."""
    today = datetime.now(timezone.utc).date()
    start_date = (today - timedelta(days=6)).isoformat()
    end_date = today.isoformat()

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum",
        "hourly": "relative_humidity_2m",
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def parse_weather_data(data: dict) -> dict:
    """Parse Open-Meteo response into averaged weather metrics."""
    daily = data.get("daily", {})
    hourly = data.get("hourly", {})

    temps_mean = [t for t in (daily.get("temperature_2m_mean") or []) if t is not None]
    temps_max = [t for t in (daily.get("temperature_2m_max") or []) if t is not None]
    precip = [p for p in (daily.get("precipitation_sum") or []) if p is not None]
    humidity_hourly = [
        h for h in (hourly.get("relative_humidity_2m") or []) if h is not None
    ]

    return {
        "temperature_avg": round(sum(temps_mean) / len(temps_mean), 1) if temps_mean else 0.0,
        "temperature_max": round(max(temps_max), 1) if temps_max else 0.0,
        "precipitation_sum": round(sum(precip), 1) if precip else 0.0,
        "precipitation_daily_avg": round(sum(precip) / len(precip), 1) if precip else 0.0,
        "relative_humidity": round(sum(humidity_hourly) / len(humidity_hourly), 1) if humidity_hourly else 0.0,
    }


async def _fetch_single_region(region: dict) -> dict:
    """Fetch and parse weather for a single region with fallback."""
    try:
        raw_data = await fetch_region_weather(
            region["latitude"], region["longitude"]
        )
        parsed = parse_weather_data(raw_data)
        return {
            "region_name": region["region_name"],
            "country": region["country"],
            "latitude": region["latitude"],
            "longitude": region["longitude"],
            **parsed,
        }
    except Exception:
        logger.exception("Failed to fetch weather data, using fallback")
        return {
            "region_name": region["region_name"],
            "country": region["country"],
            "latitude": region["latitude"],
            "longitude": region["longitude"],
            "temperature_avg": 30.0,
            "temperature_max": 38.0,
            "precipitation_sum": 7.0,
            "precipitation_daily_avg": 1.0,
            "relative_humidity": 35.0,
        }


async def get_all_weather() -> dict[str, list[dict]]:
    """Fetch weather for all commodity regions in parallel."""
    all_tasks: list[tuple[str, dict]] = []
    for commodity, regions in COMMODITY_REGIONS.items():
        for region in regions:
            all_tasks.append((commodity, region))

    fetched = await asyncio.gather(
        *[_fetch_single_region(region) for _, region in all_tasks]
    )

    results: dict[str, list[dict]] = {}
    for (commodity, _), weather in zip(all_tasks, fetched):
        if commodity not in results:
            results[commodity] = []
        results[commodity].append(weather)

    return results
