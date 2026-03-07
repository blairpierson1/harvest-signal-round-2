export type Signal = "Bullish" | "Bearish" | "Neutral";
export type Confidence = "High" | "Medium" | "Low";
export type WeatherRisk = "Normal" | "Watch" | "Alert";

export interface RegionWeather {
  region_name: string;
  country: string;
  latitude: number;
  longitude: number;
  temperature_avg: number;
  temperature_max: number;
  precipitation_sum: number;
  relative_humidity: number;
  condition_summary: string;
}

export interface PriceTrend {
  current_price: number | null;
  change_percent: number | null;
  direction: string;
  source: string;
}

export interface PriceHistoryPoint {
  date: string;
  close: number;
}

export interface PriceHistory {
  points: PriceHistoryPoint[];
  trend_label: string;
  source: string;
}

export interface ProducerCountry {
  country: string;
  share_percent: number;
  weather_risk: WeatherRisk;
  risk_detail: string;
  temperature_avg: number;
  precipitation_sum: number;
  relative_humidity: number;
}

export interface NewsHeadline {
  title: string;
  source: string;
  url: string;
  published_at: string;
}

export interface ForecastDirection {
  label: string;
  description: string;
}

export interface InvestmentSecurity {
  ticker: string;
  name: string;
  type: string;
  description: string;
  yahoo_finance_symbol: string | null;
  current_price: number | null;
  change_percent: number | null;
}

export interface ShippingRate {
  route: string;
  origin_port: string;
  destination_port: string;
  origin_lat: number | null;
  origin_lon: number | null;
  destination_lat: number | null;
  destination_lon: number | null;
  rate_usd: number | null;
  container_type: string;
  source: string;
}

export interface CommoditySignal {
  commodity: string;
  signal: Signal;
  confidence: Confidence;
  key_driver: string;
  rationale: string;
  price_trend: PriceTrend;
  price_history: PriceHistory;
  regions: RegionWeather[];
  producers: ProducerCountry[];
  news: NewsHeadline[];
  forecast: ForecastDirection;
  shipping: ShippingRate | null;
  investment_securities: InvestmentSecurity[];
  last_updated: string;
}

export interface DashboardResponse {
  signals: CommoditySignal[];
  generated_at: string;
}
