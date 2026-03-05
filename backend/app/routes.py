"""API routes for Harvest Signal dashboard."""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import limiter, verify_api_key
from app.forecast import generate_forecast
from app.models import (
    CommoditySignal,
    DashboardResponse,
    PriceHistory,
    PriceTrend,
    RegionWeather,
)
from app.news import fetch_all_news
from app.prices import fetch_all_prices, fetch_all_price_histories
from app.producers import fetch_all_producers
from app.shipping import fetch_all_shipping
from app.signals import analyze_region, generate_commodity_signal, generate_condition_summary
from app.vessels import fetch_all_vessels
from app.weather import get_all_weather

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "ok", "service": "Harvest Signal API", "version": "2.0.0"}


@router.get("/api/signals", response_model=DashboardResponse)
@limiter.limit("10/minute")
async def get_signals(request: Request, _auth: None = Depends(verify_api_key)):
    """Get weather-based trading signals for all tracked soft commodities."""
    try:
        # Fetch all data sources concurrently
        (
            weather_data,
            price_data,
            history_data,
            producer_data,
            news_data,
            shipping_data,
            vessel_data,
        ) = await asyncio.gather(
            get_all_weather(),
            fetch_all_prices(),
            fetch_all_price_histories(),
            fetch_all_producers(),
            fetch_all_news(),
            fetch_all_shipping(),
            fetch_all_vessels(),
        )

        signals = []
        for commodity, regions in weather_data.items():
            # Generate signal (pass producer data so country-level alerts influence signal)
            commodity_producers = producer_data.get(commodity, [])
            signal, confidence, key_driver, rationale = generate_commodity_signal(
                commodity, regions, producers=commodity_producers
            )

            # Build region weather models with condition summaries
            region_models = []
            for region in regions:
                analysis = analyze_region(commodity, region)
                condition = generate_condition_summary(analysis)
                region_models.append(
                    RegionWeather(
                        region_name=region["region_name"],
                        country=region["country"],
                        latitude=region["latitude"],
                        longitude=region["longitude"],
                        temperature_avg=region["temperature_avg"],
                        temperature_max=region["temperature_max"],
                        precipitation_sum=region["precipitation_sum"],
                        relative_humidity=region["relative_humidity"],
                        condition_summary=condition,
                    )
                )

            # Generate price forecast
            commodity_history = history_data.get(commodity, PriceHistory())
            forecast = generate_forecast(signal, commodity_history)

            commodity_signal = CommoditySignal(
                commodity=commodity,
                signal=signal,
                confidence=confidence,
                key_driver=key_driver,
                rationale=rationale,
                price_trend=price_data.get(commodity, PriceTrend()),
                price_history=commodity_history,
                regions=region_models,
                producers=producer_data.get(commodity, []),
                news=news_data.get(commodity, []),
                forecast=forecast,
                shipping=shipping_data.get(commodity),
                vessels=vessel_data.get(commodity, []),
                last_updated=datetime.now(timezone.utc).isoformat(),
            )
            signals.append(commodity_signal)

        return DashboardResponse(
            signals=signals,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except Exception:
        logger.exception("Failed to generate signals")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Please try again later.",
        )


@router.get("/api/health")
async def api_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commodities": ["Coffee", "Sugar", "Cocoa", "Orange Juice", "Lumber", "Palm Oil"],
    }
