"""Weather data fetching from Open-Meteo API."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

# Growing region coordinates for all six Middle East commodities
COMMODITY_REGIONS: dict[str, list[dict]] = {
    "Pistachios": [
        {"region_name": "Kerman Province", "country": "Iran", "latitude": 30.28, "longitude": 57.08},
        {"region_name": "Gaziantep", "country": "Turkey", "latitude": 37.07, "longitude": 37.38},
        {"region_name": "San Joaquin Valley", "country": "USA", "latitude": 36.60, "longitude": -119.80},
    ],
    "Dates": [
        {"region_name": "Medina Region", "country": "Saudi Arabia", "latitude": 24.47, "longitude": 39.61},
        {"region_name": "Basra Province", "country": "Iraq", "latitude": 30.51, "longitude": 47.81},
        {"region_name": "Siwa Oasis", "country": "Egypt", "latitude": 29.20, "longitude": 25.52},
    ],
    "Saffron": [
        {"region_name": "Khorasan Province", "country": "Iran", "latitude": 34.30, "longitude": 58.80},
        {"region_name": "Herat Province", "country": "Afghanistan", "latitude": 34.35, "longitude": 62.20},
        {"region_name": "Kashmir Valley", "country": "India", "latitude": 34.08, "longitude": 74.80},
    ],
    "Cotton": [
        {"region_name": "Southeastern Anatolia", "country": "Turkey", "latitude": 37.16, "longitude": 38.79},
        {"region_name": "Nile Delta", "country": "Egypt", "latitude": 30.90, "longitude": 31.20},
        {"region_name": "Sindh Province", "country": "Pakistan", "latitude": 25.38, "longitude": 68.37},
    ],
    "Hazelnuts": [
        {"region_name": "Black Sea Coast", "country": "Turkey", "latitude": 41.00, "longitude": 39.72},
        {"region_name": "Piemonte", "country": "Italy", "latitude": 44.69, "longitude": 8.04},
        {"region_name": "Sheki-Zagatala", "country": "Azerbaijan", "latitude": 41.19, "longitude": 47.17},
    ],
    "Olive Oil": [
        {"region_name": "Aegean Coast", "country": "Turkey", "latitude": 38.42, "longitude": 27.14},
        {"region_name": "Sfax Governorate", "country": "Tunisia", "latitude": 34.74, "longitude": 10.76},
        {"region_name": "Latakia", "country": "Syria", "latitude": 35.52, "longitude": 35.79},
    ],
}

# Typical monthly averages for reference (simplified baselines)
BASELINE_TEMP: dict[str, dict[str, float]] = {
    "Pistachios": {"Iran": 28.0, "Turkey": 22.0, "USA": 25.0},
    "Dates": {"Saudi Arabia": 35.0, "Iraq": 33.0, "Egypt": 30.0},
    "Saffron": {"Iran": 20.0, "Afghanistan": 18.0, "India": 16.0},
    "Cotton": {"Turkey": 28.0, "Egypt": 30.0, "Pakistan": 32.0},
    "Hazelnuts": {"Turkey": 18.0, "Italy": 16.0, "Azerbaijan": 17.0},
    "Olive Oil": {"Turkey": 22.0, "Tunisia": 25.0, "Syria": 24.0},
}

BASELINE_PRECIP: dict[str, dict[str, float]] = {
    "Pistachios": {"Iran": 0.5, "Turkey": 1.5, "USA": 0.3},
    "Dates": {"Saudi Arabia": 0.2, "Iraq": 0.3, "Egypt": 0.1},
    "Saffron": {"Iran": 1.0, "Afghanistan": 0.8, "India": 2.0},
    "Cotton": {"Turkey": 1.5, "Egypt": 0.2, "Pakistan": 1.0},
    "Hazelnuts": {"Turkey": 4.0, "Italy": 3.0, "Azerbaijan": 2.5},
    "Olive Oil": {"Turkey": 2.0, "Tunisia": 1.0, "Syria": 1.5},
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
    except (httpx.HTTPError, httpx.TimeoutException, KeyError, IndexError, ValueError, TypeError, AttributeError):
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
