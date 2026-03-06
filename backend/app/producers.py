"""Top producing countries with weather risk assessment for each commodity."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.models import ProducerCountry, WeatherRisk

logger = logging.getLogger(__name__)

# Top producing countries for Middle East commodities with primary growing region coordinates and regional share.
PRODUCER_CONFIG: dict[str, list[dict]] = {
    "Pistachios": [
        {"country": "Iran", "share_percent": 45.0, "latitude": 30.28, "longitude": 57.08},
        {"country": "Turkey", "share_percent": 20.0, "latitude": 37.07, "longitude": 37.38},
        {"country": "Saudi Arabia", "share_percent": 3.0, "latitude": 24.71, "longitude": 46.68},
        {"country": "Lebanon", "share_percent": 1.5, "latitude": 33.89, "longitude": 35.50},
        {"country": "Jordan", "share_percent": 1.0, "latitude": 31.95, "longitude": 35.93},
    ],
    "Figs": [
        {"country": "Turkey", "share_percent": 28.0, "latitude": 37.85, "longitude": 27.85},
        {"country": "Iran", "share_percent": 15.0, "latitude": 29.62, "longitude": 52.53},
        {"country": "Saudi Arabia", "share_percent": 5.0, "latitude": 24.47, "longitude": 39.61},
        {"country": "Iraq", "share_percent": 4.0, "latitude": 33.31, "longitude": 44.37},
        {"country": "Lebanon", "share_percent": 2.0, "latitude": 33.85, "longitude": 35.90},
    ],
    "Olives": [
        {"country": "Turkey", "share_percent": 20.0, "latitude": 38.42, "longitude": 27.14},
        {"country": "Israel", "share_percent": 3.0, "latitude": 32.82, "longitude": 35.17},
        {"country": "Jordan", "share_percent": 4.0, "latitude": 32.33, "longitude": 35.75},
        {"country": "Lebanon", "share_percent": 3.5, "latitude": 33.85, "longitude": 35.90},
        {"country": "Iraq", "share_percent": 1.5, "latitude": 36.34, "longitude": 43.13},
    ],
    "Dates": [
        {"country": "Saudi Arabia", "share_percent": 17.0, "latitude": 25.38, "longitude": 49.59},
        {"country": "Iraq", "share_percent": 15.0, "latitude": 30.51, "longitude": 47.81},
        {"country": "Iran", "share_percent": 14.0, "latitude": 31.32, "longitude": 48.67},
        {"country": "Israel", "share_percent": 3.0, "latitude": 31.25, "longitude": 35.38},
        {"country": "Jordan", "share_percent": 2.0, "latitude": 29.53, "longitude": 35.01},
    ],
    "Citrus": [
        {"country": "Turkey", "share_percent": 15.0, "latitude": 36.90, "longitude": 30.70},
        {"country": "Iran", "share_percent": 8.0, "latitude": 36.77, "longitude": 53.06},
        {"country": "Israel", "share_percent": 5.0, "latitude": 32.08, "longitude": 34.78},
        {"country": "Lebanon", "share_percent": 3.0, "latitude": 33.85, "longitude": 35.90},
        {"country": "Iraq", "share_percent": 2.0, "latitude": 35.47, "longitude": 44.39},
    ],
}

# Commodity-specific thresholds for weather risk classification.
RISK_THRESHOLDS: dict[str, dict[str, float]] = {
    "Pistachios": {"temp_watch": 38.0, "temp_alert": 44.0, "precip_low_watch": 0.5, "precip_low_alert": 0.2, "precip_high_watch": 5.0, "precip_high_alert": 10.0, "humidity_low": 20.0},
    "Figs": {"temp_watch": 35.0, "temp_alert": 42.0, "precip_low_watch": 0.8, "precip_low_alert": 0.3, "precip_high_watch": 6.0, "precip_high_alert": 12.0, "humidity_low": 25.0},
    "Olives": {"temp_watch": 34.0, "temp_alert": 40.0, "precip_low_watch": 1.0, "precip_low_alert": 0.4, "precip_high_watch": 7.0, "precip_high_alert": 14.0, "humidity_low": 25.0},
    "Dates": {"temp_watch": 45.0, "temp_alert": 50.0, "precip_low_watch": 0.2, "precip_low_alert": 0.05, "precip_high_watch": 3.0, "precip_high_alert": 8.0, "humidity_low": 15.0},
    "Citrus": {"temp_watch": 33.0, "temp_alert": 38.0, "precip_low_watch": 1.0, "precip_low_alert": 0.4, "precip_high_watch": 8.0, "precip_high_alert": 15.0, "humidity_low": 30.0},
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
        "temperature_avg": round(sum(temps_mean) / len(temps_mean), 1) if temps_mean else 28.0,
        "temperature_max": round(max(temps_max), 1) if temps_max else 32.0,
        "precipitation_sum": round(sum(precip), 1) if precip else 7.0,
        "precipitation_daily_avg": round(sum(precip) / len(precip), 1) if precip else 1.0,
        "relative_humidity": round(sum(humidity_hourly) / len(humidity_hourly), 1) if humidity_hourly else 35.0,
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
        weather = {
            "temperature_avg": 28.0,
            "temperature_max": 32.0,
            "precipitation_sum": 7.0,
            "precipitation_daily_avg": 1.0,
            "relative_humidity": 35.0,
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
