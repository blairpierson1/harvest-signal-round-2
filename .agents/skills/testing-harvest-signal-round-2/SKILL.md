# Testing Harvest Signal Round 2

## Overview
Harvest Signal Round 2 is a soft commodity weather signal dashboard tracking 6 commodities: Pistachios, Dates, Saffron, Cotton, Hazelnuts, and Olive Oil. The app has a FastAPI backend and Next.js frontend.

## Local Setup

### Backend
```bash
cd ~/repos/harvest-signal-round-2/backend
DISABLE_AUTH=true poetry run fastapi dev app/main.py
```
- Runs at http://localhost:8000
- **Important**: You must set `DISABLE_AUTH=true` or the API will return 500 errors on every request. Without this env var and without `API_KEY` set, the `verify_api_key` dependency in `dependencies.py` rejects all requests.
- Weather data (Open-Meteo) and Yahoo Finance prices work without API keys.
- The `NEWSAPI_KEY` secret is needed for news headlines but the app works without it (news section will be empty).

### Frontend
```bash
cd ~/repos/harvest-signal-round-2/frontend
npm run dev
```
- Runs at http://localhost:3000
- Connects to backend via `NEXT_PUBLIC_API_URL` in `.env.local` (defaults to `http://localhost:8000`)

### Linting
```bash
cd ~/repos/harvest-signal-round-2/frontend && npm run lint
```

## Dashboard Structure
- The main page loads at `/` and shows a map + 6 commodity cards in a 3x2 grid
- Each card shows: signal badge (Bullish/Bearish/Neutral), key driver, price, confidence, sparkline chart, forecast, investment exposure securities, shipping rate, news, rationale
- Cards have expandable sections for region details and producer countries
- Data auto-refreshes every 5 minutes

## Testing Patterns

### Verifying API Response
The backend `/api/signals` endpoint returns a `DashboardResponse` with a list of `CommoditySignal` objects. You can test the API directly:
```bash
curl http://localhost:8000/api/signals
```
Note: This only works if `DISABLE_AUTH=true` is set.

### UI Verification
- Wait ~10-15 seconds after loading for the backend to fetch all weather/price data from external APIs
- Scroll through all 6 commodity cards to verify each section renders
- Tickers in the Investment Exposure section link to Yahoo Finance (opens in new tab)
- Price change percentages are color-coded: green for positive, red for negative
- Securities with `null` yahoo_finance_symbol will show no price data (this is expected, not a bug)

### Common Issues
- If cards show loading skeletons indefinitely, check the backend terminal for errors
- Yahoo Finance requests may occasionally fail/timeout — the app gracefully degrades to showing no price
- The backend fetches data from many external APIs in parallel (Open-Meteo, Yahoo Finance, NewsAPI, Freightos) — initial load can take 5-15 seconds depending on API response times

## Default Branch
The default branch is `devin/1772737143-full-app-build` (not `main`).

## Devin Secrets Needed
- `NEWSAPI_KEY` — For fetching commodity news headlines (optional, app works without it)
