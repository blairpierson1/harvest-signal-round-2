"""Top producing countries with weather risk assessment for each commodity."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.models import ProducerCountry, WeatherRisk

logger = logging.getLogger(__name__)

# Top 5 producing countries with primary growing region coordinates and global share.
PRODUCER_CONFIG: dict[str, list[dict]] = {
    "Pistachios": [
        {"country": "Iran", "share_percent": 40.0, "latitude": 30.28, "longitude": 57.08},
        {"country": "USA", "share_percent": 28.0, "latitude": 36.60, "longitude": -119.80},
        {"country": "Turkey", "share_percent": 15.0, "latitude": 37.07, "longitude": 37.38},
        {"country": "China", "share_percent": 5.0, "latitude": 37.80, "longitude": 75.00},
        {"country": "Syria", "share_percent": 3.0, "latitude": 36.20, "longitude": 37.16},
    ],
    "Dates": [
        {"country": "Egypt", "share_percent": 18.0, "latitude": 29.20, "longitude": 25.52},
        {"country": "Saudi Arabia", "share_percent": 15.0, "latitude": 24.47, "longitude": 39.61},
        {"country": "Iran", "share_percent": 14.0, "latitude": 27.18, "longitude": 53.68},
        {"country": "Algeria", "share_percent": 12.0, "latitude": 34.05, "longitude": 5.73},
        {"country": "Iraq", "share_percent": 8.0, "latitude": 30.51, "longitude": 47.81},
    ],
    "Saffron": [
        {"country": "Iran", "share_percent": 90.0, "latitude": 34.30, "longitude": 58.80},
        {"country": "India", "share_percent": 4.0, "latitude": 34.08, "longitude": 74.80},
        {"country": "Afghanistan", "share_percent": 3.0, "latitude": 34.35, "longitude": 62.20},
        {"country": "Spain", "share_percent": 1.5, "latitude": 38.99, "longitude": -1.86},
        {"country": "Morocco", "share_percent": 1.0, "latitude": 31.63, "longitude": -8.01},
    ],
    "Cotton": [
        {"country": "Turkey", "share_percent": 5.0, "latitude": 37.16, "longitude": 38.79},
        {"country": "Egypt", "share_percent": 2.0, "latitude": 30.90, "longitude": 31.20},
        {"country": "Pakistan", "share_percent": 8.0, "latitude": 25.38, "longitude": 68.37},
        {"country": "India", "share_percent": 25.0, "latitude": 21.15, "longitude": 79.09},
        {"country": "Uzbekistan", "share_percent": 4.0, "latitude": 40.10, "longitude": 65.37},
    ],
    "Hazelnuts": [
        {"country": "Turkey", "share_percent": 70.0, "latitude": 41.00, "longitude": 39.72},
        {"country": "Italy", "share_percent": 13.0, "latitude": 44.69, "longitude": 8.04},
        {"country": "Azerbaijan", "share_percent": 5.0, "latitude": 41.19, "longitude": 47.17},
        {"country": "USA", "share_percent": 4.0, "latitude": 45.52, "longitude": -122.68},
        {"country": "Georgia", "share_percent": 3.0, "latitude": 42.27, "longitude": 42.70},
    ],
    "Olive Oil": [
        {"country": "Turkey", "share_percent": 15.0, "latitude": 38.42, "longitude": 27.14},
        {"country": "Tunisia", "share_percent": 10.0, "latitude": 34.74, "longitude": 10.76},
        {"country": "Syria", "share_percent": 5.0, "latitude": 35.52, "longitude": 35.79},
        {"country": "Morocco", "share_percent": 5.0, "latitude": 31.63, "longitude": -8.01},
        {"country": "Jordan", "share_percent": 2.0, "latitude": 32.06, "longitude": 36.09},
    ],
}

# Commodity-specific thresholds for weather risk classification.
RISK_THRESHOLDS: dict[str, dict[str, float]] = {
    "Pistachios": {"temp_watch": 40.0, "temp_alert": 46.0, "precip_low_watch": 0.08, "precip_low_alert": 0.02, "precip_high_watch": 6.0, "precip_high_alert": 10.0, "humidity_low": 10.0},
    "Dates": {"temp_watch": 48.0, "temp_alert": 52.0, "precip_low_watch": 0.02, "precip_low_alert": 0.005, "precip_high_watch": 3.0, "precip_high_alert": 6.0, "humidity_low": 8.0},
    "Saffron": {"temp_watch": 32.0, "temp_alert": 38.0, "precip_low_watch": 0.15, "precip_low_alert": 0.05, "precip_high_watch": 6.0, "precip_high_alert": 10.0, "humidity_low": 15.0},
    "Cotton": {"temp_watch": 40.0, "temp_alert": 46.0, "precip_low_watch": 0.15, "precip_low_alert": 0.05, "precip_high_watch": 8.0, "precip_high_alert": 14.0, "humidity_low": 15.0},
    "Hazelnuts": {"temp_watch": 32.0, "temp_alert": 37.0, "precip_low_watch": 2.0, "precip_low_alert": 1.0, "precip_high_watch": 12.0, "precip_high_alert": 18.0, "humidity_low": 40.0},
    "Olive Oil": {"temp_watch": 38.0, "temp_alert": 44.0, "precip_low_watch": 0.15, "precip_low_alert": 0.05, "precip_high_watch": 8.0, "precip_high_alert": 12.0, "humidity_low": 15.0},
}


async def _fetch_producer_weather(latitude: float, longitude: float) -> dict:
    """Fetch 7-day weather for a producer country's primary growing region."""
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
        data = response.json()

    daily = data.get("daily", {})
    hourly = data.get("hourly", {})

    temps_mean = [t for t in (daily.get("temperature_2m_mean") or []) if t is not None]
    temps_max = [t for t in (daily.get("temperature_2m_max") or []) if t is not None]
    precip = [p for p in (daily.get("precipitation_sum") or []) if p is not None]
    humidity_hourly = [h for h in (hourly.get("relative_humidity_2m") or []) if h is not None]

    return {
        "temperature_avg": round(sum(temps_mean) / len(temps_mean), 1) if temps_mean else 25.0,
        "temperature_max": round(max(temps_max), 1) if temps_max else 32.0,
        "precipitation_sum": round(sum(precip), 1) if precip else 20.0,
        "precipitation_daily_avg": round(sum(precip) / len(precip), 1) if precip else 2.9,
        "relative_humidity": round(sum(humidity_hourly) / len(humidity_hourly), 1) if humidity_hourly else 70.0,
    }


def _classify_risk(commodity: str, weather: dict) -> tuple[WeatherRisk, str]:
    """Classify weather risk for a producer country as Normal/Watch/Alert."""
    t = RISK_THRESHOLDS[commodity]
    temp_max = weather["temperature_max"]
    precip_daily = weather["precipitation_daily_avg"]
    humidity = weather["relative_humidity"]

    alerts: list[str] = []
    watches: list[str] = []

    if temp_max > t["temp_alert"]:
        alerts.append(f"Extreme heat ({temp_max:.0f}C)")
    elif temp_max > t["temp_watch"]:
        watches.append(f"Elevated temps ({temp_max:.0f}C)")

    if precip_daily < t["precip_low_alert"]:
        alerts.append(f"Very low rainfall ({precip_daily:.1f}mm/day)")
    elif precip_daily < t["precip_low_watch"]:
        watches.append(f"Below-avg rainfall ({precip_daily:.1f}mm/day)")

    if precip_daily > t["precip_high_alert"]:
        alerts.append(f"Heavy rainfall ({precip_daily:.1f}mm/day)")
    elif precip_daily > t["precip_high_watch"]:
        watches.append(f"Above-avg rainfall ({precip_daily:.1f}mm/day)")

    if humidity < t["humidity_low"]:
        watches.append(f"Low humidity ({humidity:.0f}%)")

    if alerts:
        return WeatherRisk.ALERT, "; ".join(alerts)
    elif watches:
        return WeatherRisk.WATCH, "; ".join(watches)
    return WeatherRisk.NORMAL, "Conditions within normal range"


async def _fetch_single_producer(commodity: str, config: dict) -> ProducerCountry:
    """Fetch weather and classify risk for a single producer country."""
    try:
        weather = await _fetch_producer_weather(config["latitude"], config["longitude"])
    except Exception:
        logger.exception("Failed to fetch producer data, using fallback")
        # Fallback values are intentionally moderate so they classify as Normal
        # risk rather than inadvertently triggering Watch/Alert status.
        weather = {
            "temperature_avg": 22.0,
            "temperature_max": 28.0,
            "precipitation_sum": 20.0,
            "precipitation_daily_avg": 3.0,
            "relative_humidity": 55.0,
        }

    risk, detail = _classify_risk(commodity, weather)

    return ProducerCountry(
        country=config["country"],
        share_percent=config["share_percent"],
        weather_risk=risk,
        risk_detail=detail,
        temperature_avg=weather["temperature_avg"],
        precipitation_sum=weather["precipitation_sum"],
        relative_humidity=weather["relative_humidity"],
    )


async def fetch_all_producers() -> dict[str, list[ProducerCountry]]:
    """Fetch weather risk for all producer countries across all commodities."""
    all_tasks: list[tuple[str, dict]] = []
    for commodity, producers in PRODUCER_CONFIG.items():
        for producer in producers:
            all_tasks.append((commodity, producer))

    results = await asyncio.gather(
        *[_fetch_single_producer(commodity, config) for commodity, config in all_tasks]
    )

    grouped: dict[str, list[ProducerCountry]] = {}
    for (commodity, _), producer in zip(all_tasks, results):
        if commodity not in grouped:
            grouped[commodity] = []
        grouped[commodity].append(producer)

    return grouped
