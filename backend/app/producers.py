"""Top producing countries with weather risk assessment for each commodity."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.models import ProducerCountry, WeatherRisk

logger = logging.getLogger(__name__)

# Top 5 producing countries with primary growing region coordinates and global share.
PRODUCER_CONFIG: dict[str, list[dict]] = {
    "Coffee": [
        {"country": "Brazil", "share_percent": 37.4, "latitude": -18.51, "longitude": -44.55},
        {"country": "Vietnam", "share_percent": 17.4, "latitude": 14.35, "longitude": 108.00},
        {"country": "Colombia", "share_percent": 7.2, "latitude": 4.60, "longitude": -75.80},
        {"country": "Indonesia", "share_percent": 6.6, "latitude": -2.50, "longitude": 115.00},
        {"country": "Ethiopia", "share_percent": 4.5, "latitude": 7.00, "longitude": 38.00},
    ],
    "Sugar": [
        {"country": "Brazil", "share_percent": 21.0, "latitude": -22.19, "longitude": -48.79},
        {"country": "India", "share_percent": 18.5, "latitude": 27.18, "longitude": 80.35},
        {"country": "Thailand", "share_percent": 5.8, "latitude": 14.88, "longitude": 100.00},
        {"country": "China", "share_percent": 5.5, "latitude": 23.83, "longitude": 108.33},
        {"country": "Pakistan", "share_percent": 3.6, "latitude": 30.20, "longitude": 71.50},
    ],
    "Cocoa": [
        {"country": "Ivory Coast", "share_percent": 38.2, "latitude": 5.28, "longitude": -6.58},
        {"country": "Ghana", "share_percent": 17.0, "latitude": 6.75, "longitude": -1.52},
        {"country": "Indonesia", "share_percent": 5.1, "latitude": -1.50, "longitude": 120.50},
        {"country": "Nigeria", "share_percent": 4.8, "latitude": 7.50, "longitude": 3.90},
        {"country": "Ecuador", "share_percent": 4.5, "latitude": -1.80, "longitude": -79.50},
    ],
    "Orange Juice": [
        {"country": "Brazil", "share_percent": 30.0, "latitude": -22.19, "longitude": -48.79},
        {"country": "USA", "share_percent": 15.0, "latitude": 28.54, "longitude": -81.38},
        {"country": "Mexico", "share_percent": 8.0, "latitude": 19.17, "longitude": -96.13},
        {"country": "Spain", "share_percent": 6.0, "latitude": 39.47, "longitude": -0.38},
        {"country": "Italy", "share_percent": 4.0, "latitude": 37.50, "longitude": 15.09},
    ],
    "Lumber": [
        {"country": "USA", "share_percent": 18.0, "latitude": 47.61, "longitude": -122.33},
        {"country": "Canada", "share_percent": 15.0, "latitude": 49.28, "longitude": -123.12},
        {"country": "Russia", "share_percent": 12.0, "latitude": 56.32, "longitude": 44.00},
        {"country": "Sweden", "share_percent": 5.0, "latitude": 59.33, "longitude": 18.07},
        {"country": "Finland", "share_percent": 4.0, "latitude": 60.17, "longitude": 24.94},
    ],
    "Palm Oil": [
        {"country": "Indonesia", "share_percent": 58.0, "latitude": 0.51, "longitude": 101.45},
        {"country": "Malaysia", "share_percent": 26.0, "latitude": 5.98, "longitude": 116.07},
        {"country": "Thailand", "share_percent": 4.0, "latitude": 8.96, "longitude": 99.10},
        {"country": "Colombia", "share_percent": 2.5, "latitude": 7.12, "longitude": -73.12},
        {"country": "Nigeria", "share_percent": 2.0, "latitude": 6.52, "longitude": 3.38},
    ],
}

# Commodity-specific thresholds for weather risk classification.
RISK_THRESHOLDS: dict[str, dict[str, float]] = {
    "Coffee": {"temp_watch": 28.0, "temp_alert": 32.0, "precip_low_watch": 2.0, "precip_low_alert": 1.0, "precip_high_watch": 10.0, "precip_high_alert": 14.0, "humidity_low": 50.0},
    "Sugar": {"temp_watch": 32.0, "temp_alert": 36.0, "precip_low_watch": 2.0, "precip_low_alert": 1.0, "precip_high_watch": 12.0, "precip_high_alert": 16.0, "humidity_low": 45.0},
    "Cocoa": {"temp_watch": 30.0, "temp_alert": 34.0, "precip_low_watch": 2.5, "precip_low_alert": 1.5, "precip_high_watch": 12.0, "precip_high_alert": 15.0, "humidity_low": 55.0},
    "Orange Juice": {"temp_watch": 30.0, "temp_alert": 35.0, "precip_low_watch": 2.0, "precip_low_alert": 1.0, "precip_high_watch": 12.0, "precip_high_alert": 16.0, "humidity_low": 45.0},
    "Lumber": {"temp_watch": 30.0, "temp_alert": 38.0, "precip_low_watch": 1.5, "precip_low_alert": 0.5, "precip_high_watch": 15.0, "precip_high_alert": 22.0, "humidity_low": 30.0},
    "Palm Oil": {"temp_watch": 31.0, "temp_alert": 35.0, "precip_low_watch": 3.5, "precip_low_alert": 2.0, "precip_high_watch": 14.0, "precip_high_alert": 20.0, "humidity_low": 60.0},
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
        weather = {
            "temperature_avg": 25.0,
            "temperature_max": 32.0,
            "precipitation_sum": 20.0,
            "precipitation_daily_avg": 2.9,
            "relative_humidity": 70.0,
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
