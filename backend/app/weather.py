"""Weather data fetching from Open-Meteo API."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

# Growing region coordinates for all six commodities
COMMODITY_REGIONS: dict[str, list[dict]] = {
    "Coffee": [
        {"region_name": "Minas Gerais", "country": "Brazil", "latitude": -18.51, "longitude": -44.55},
        {"region_name": "Sao Paulo State", "country": "Brazil", "latitude": -22.19, "longitude": -48.79},
        {"region_name": "Central Highlands", "country": "Vietnam", "latitude": 14.35, "longitude": 108.00},
    ],
    "Sugar": [
        {"region_name": "Sao Paulo State", "country": "Brazil", "latitude": -22.19, "longitude": -48.79},
        {"region_name": "Ribeirao Preto", "country": "Brazil", "latitude": -21.18, "longitude": -47.81},
        {"region_name": "Uttar Pradesh", "country": "India", "latitude": 27.18, "longitude": 80.35},
    ],
    "Cocoa": [
        {"region_name": "Ashanti Region", "country": "Ghana", "latitude": 6.75, "longitude": -1.52},
        {"region_name": "Western Region", "country": "Ghana", "latitude": 5.50, "longitude": -2.50},
        {"region_name": "Bas-Sassandra", "country": "Ivory Coast", "latitude": 5.28, "longitude": -6.58},
    ],
    "Orange Juice": [
        {"region_name": "Central Florida", "country": "USA", "latitude": 28.54, "longitude": -81.38},
        {"region_name": "Sao Paulo State", "country": "Brazil", "latitude": -22.19, "longitude": -48.79},
        {"region_name": "Veracruz", "country": "Mexico", "latitude": 19.17, "longitude": -96.13},
    ],
    "Lumber": [
        {"region_name": "Pacific Northwest", "country": "USA", "latitude": 47.61, "longitude": -122.33},
        {"region_name": "British Columbia", "country": "Canada", "latitude": 49.28, "longitude": -123.12},
        {"region_name": "Southeast USA", "country": "USA", "latitude": 33.75, "longitude": -84.39},
    ],
    "Palm Oil": [
        {"region_name": "Riau Province", "country": "Indonesia", "latitude": 0.51, "longitude": 101.45},
        {"region_name": "North Sumatra", "country": "Indonesia", "latitude": 3.59, "longitude": 98.67},
        {"region_name": "Sabah", "country": "Malaysia", "latitude": 5.98, "longitude": 116.07},
    ],
}

# Typical monthly averages for reference (simplified baselines)
BASELINE_TEMP: dict[str, dict[str, float]] = {
    "Coffee": {"Brazil": 23.0, "Vietnam": 24.0},
    "Sugar": {"Brazil": 24.0, "India": 28.0},
    "Cocoa": {"Ghana": 27.0, "Ivory Coast": 27.0},
    "Orange Juice": {"USA": 24.0, "Brazil": 24.0, "Mexico": 25.0},
    "Lumber": {"USA": 12.0, "Canada": 10.0},
    "Palm Oil": {"Indonesia": 27.0, "Malaysia": 27.0},
}

BASELINE_PRECIP: dict[str, dict[str, float]] = {
    "Coffee": {"Brazil": 5.0, "Vietnam": 6.0},
    "Sugar": {"Brazil": 4.5, "India": 3.0},
    "Cocoa": {"Ghana": 5.5, "Ivory Coast": 6.0},
    "Orange Juice": {"USA": 5.0, "Brazil": 4.5, "Mexico": 4.0},
    "Lumber": {"USA": 4.0, "Canada": 3.5},
    "Palm Oil": {"Indonesia": 7.0, "Malaysia": 7.0},
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
            "temperature_avg": 25.0,
            "temperature_max": 32.0,
            "precipitation_sum": 20.0,
            "precipitation_daily_avg": 2.9,
            "relative_humidity": 70.0,
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
