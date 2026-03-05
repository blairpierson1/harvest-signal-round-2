from enum import Enum
from pydantic import BaseModel


class Signal(str, Enum):
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class WeatherRisk(str, Enum):
    NORMAL = "Normal"
    WATCH = "Watch"
    ALERT = "Alert"


class RegionWeather(BaseModel):
    region_name: str
    country: str
    latitude: float
    longitude: float
    temperature_avg: float
    temperature_max: float
    precipitation_sum: float
    relative_humidity: float
    condition_summary: str


class PriceTrend(BaseModel):
    current_price: float | None = None
    change_percent: float | None = None
    direction: str = "N/A"
    source: str = "estimated"


class PriceHistoryPoint(BaseModel):
    date: str
    close: float


class PriceHistory(BaseModel):
    points: list[PriceHistoryPoint] = []
    trend_label: str = "N/A"
    source: str = "yahoo_finance"


class ProducerCountry(BaseModel):
    country: str
    share_percent: float
    weather_risk: WeatherRisk
    risk_detail: str
    temperature_avg: float
    precipitation_sum: float
    relative_humidity: float


class NewsHeadline(BaseModel):
    title: str
    source: str
    url: str
    published_at: str


class ForecastDirection(BaseModel):
    label: str
    description: str


class ShippingRate(BaseModel):
    route: str
    origin_port: str
    destination_port: str
    rate_usd: float | None = None
    container_type: str = "40ft"
    source: str = "freightos"


class Vessel(BaseModel):
    name: str
    mmsi: str
    imo: str | None = None
    vessel_type: str
    cargo: str
    latitude: float
    longitude: float
    speed_knots: float
    heading: float
    status: str
    destination_port: str
    origin_port: str
    eta: str | None = None
    route_coords: list[list[float]] = []
    source: str = "simulated"


class CommoditySignal(BaseModel):
    commodity: str
    signal: Signal
    confidence: Confidence
    key_driver: str
    rationale: str
    price_trend: PriceTrend
    price_history: PriceHistory
    regions: list[RegionWeather]
    producers: list[ProducerCountry]
    news: list[NewsHeadline] = []
    forecast: ForecastDirection = ForecastDirection(
        label="N/A", description="Insufficient data"
    )
    shipping: ShippingRate | None = None
    vessels: list[Vessel] = []
    last_updated: str


class DashboardResponse(BaseModel):
    signals: list[CommoditySignal]
    generated_at: str
