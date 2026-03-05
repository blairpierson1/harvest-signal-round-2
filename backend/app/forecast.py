"""Price forecast direction combining weather signal with price trend."""

from app.models import ForecastDirection, PriceHistory, Signal


def generate_forecast(
    signal: Signal,
    price_history: PriceHistory,
) -> ForecastDirection:
    """Generate a price forecast direction combining weather signal with price trend.

    Logic:
    - Bullish signal + Uptrend => Strong Up
    - Bullish signal + Downtrend/Sideways => Likely Up (weather divergence)
    - Bearish signal + Downtrend => Strong Down
    - Bearish signal + Uptrend/Sideways => Likely Down (weather divergence)
    - Neutral signal => follows existing trend or Sideways
    """
    trend = price_history.trend_label

    if signal == Signal.BULLISH:
        if trend == "Uptrend":
            return ForecastDirection(
                label="Strong Up",
                description="Weather-driven supply risk aligns with upward price momentum.",
            )
        elif trend == "Downtrend":
            return ForecastDirection(
                label="Likely Up",
                description="Weather risk signals potential reversal from current downtrend.",
            )
        else:
            return ForecastDirection(
                label="Likely Up",
                description="Supply-side weather risk suggests upward price pressure ahead.",
            )

    elif signal == Signal.BEARISH:
        if trend == "Downtrend":
            return ForecastDirection(
                label="Strong Down",
                description="Harvest disruption concerns align with downward price momentum.",
            )
        elif trend == "Uptrend":
            return ForecastDirection(
                label="Likely Down",
                description="Excess rainfall may cap upside and pressure prices lower.",
            )
        else:
            return ForecastDirection(
                label="Likely Down",
                description="Weather conditions suggest downward pressure on prices.",
            )

    else:  # Neutral
        if trend == "Uptrend":
            return ForecastDirection(
                label="Steady Up",
                description="Normal weather with existing upward momentum likely continues.",
            )
        elif trend == "Downtrend":
            return ForecastDirection(
                label="Steady Down",
                description="Normal weather with existing downward momentum likely continues.",
            )
        else:
            return ForecastDirection(
                label="Sideways",
                description="No significant weather or price catalysts; range-bound expected.",
            )
