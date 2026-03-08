# Testing Harvest Signal Dashboard

## Local App Testing

### Starting the App
1. **Backend**: `cd ~/repos/harvest-signal-round-2/backend && poetry run fastapi dev app/main.py` (runs on http://localhost:8000)
2. **Frontend**: `cd ~/repos/harvest-signal-round-2/frontend && npm run dev` (runs on http://localhost:3000)

No API keys required for core functionality (weather + prices). The `NEWSAPI_KEY` secret is needed for news headlines.

### Linting
```bash
cd ~/repos/harvest-signal-round-2/frontend && npm run lint
```

### What to Test

#### Map (MapView.tsx)
- Verify growing region markers (colored circles) render on the world map
- Verify shipping lane polylines (dashed lines) connect origin/destination ports
- Verify sky-blue port markers appear at shipping endpoints
- Click region markers to verify popups show commodity name, signal, and weather data
- Click shipping lanes to verify popups show route name, port codes, and freight rate
- Check the legend shows: Bullish, Bearish, Neutral, Shipping entries
- **Note**: Polylines are thin (weight: 2) and can be hard to click precisely

#### Commodity Cards (CommodityCard.tsx)
- All 6 commodities should display: Coffee, Sugar, Cocoa, Orange Juice, Lumber, Palm Oil
- Each card shows: signal badge, key driver, price, confidence, sparkline, forecast, shipping route, rationale
- Shipping line shows route name (e.g., "Santos to New York") and rate or "N/A"

#### Data Refresh
- Click the "Refresh" button in the header
- Status indicator should change to "LOADING" then back to "LIVE"
- "Last updated" timestamp should update
- Map markers and shipping lanes should re-render without duplication

### Key Routes
- Shipping routes: Santos-New York (Coffee), Santos-Rotterdam (Sugar, OJ), Abidjan-Rotterdam (Cocoa), Vancouver-Shanghai (Lumber), Belawan-Rotterdam (Palm Oil)
