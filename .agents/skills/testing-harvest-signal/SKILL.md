# Testing Harvest Signal Dashboard

## Overview
Full-stack soft commodity weather signal dashboard with FastAPI backend and Next.js frontend.

## Devin Secrets Needed
- `NEWSAPI_KEY` — Required for news headlines in commodity cards. Without it, news sections will be empty but the app still functions.

## Local Dev Setup

### Backend (port 8000)
```bash
cd backend
poetry install
# Create .env with NEWSAPI_KEY=${NEWSAPI_KEY}
echo "NEWSAPI_KEY=${NEWSAPI_KEY}" > .env
poetry run fastapi dev app/main.py
```
- No `API_KEY` env var needed for local dev (auth is disabled when not set)
- Backend serves on http://localhost:8000
- Health check: `curl http://localhost:8000/api/health`
- Main data endpoint: `GET /api/signals` (rate limited to 10/min)

### Frontend (port 3000)
```bash
cd frontend
npm install
npm run dev
```
- Frontend serves on http://localhost:3000
- Fetches data from `NEXT_PUBLIC_API_URL` env var, defaults to `http://localhost:8000`
- CORS is configured to allow localhost:3000

## Key Verification Steps

1. **Map loads at top of dashboard** — This is the CRITICAL requirement. The Leaflet map should show "Global Growing Regions (18 regions tracked)" with colored circle markers. If map doesn't load, check:
   - Leaflet npm package installed (`npm ls leaflet`)
   - CDN for leaflet CSS is reachable (unpkg.com)
   - No SSR issues (MapView is dynamically imported with `ssr: false`)

2. **All 6 commodity cards visible** — Coffee, Sugar, Cocoa, Orange Juice, Lumber, Palm Oil in a 2x3 grid

3. **Each card shows**: Signal badge, price ticker, 30-day sparkline, forecast direction, shipping route, news headlines, rationale, expandable region details and producer countries

4. **Map marker popups** — Click any green/red/orange dot to see commodity name, region, signal, temperature, precipitation, humidity

5. **Header** — Shows signal summary counts (e.g. "6 Bull") and LIVE status indicator

## Common Issues
- **Shipping rates show N/A**: Freightos public API often returns null for `rate_usd` — this is expected
- **Lumber price history unavailable**: Yahoo Finance may not have historical data for LBS=F — sparkline will show "Price history unavailable"
- **Palm Oil uses ZL=F (Soybean Oil) as proxy**: FCPO (actual Palm Oil futures) isn't available on Yahoo Finance
- **News empty without NEWSAPI_KEY**: Graceful degradation, no errors thrown
- **E402 lint warnings in main.py**: `load_dotenv()` before imports is intentional, ignore these
- **Frontend `npm run lint` fails**: The lint script is configured as just `eslint` with no directory argument — this is a pre-existing config issue, not related to code changes. Use `npx tsc --noEmit` for type checking instead.

## API Sources (single source each, no waterfall)
- Weather: Open-Meteo (free, no key)
- Prices: Yahoo Finance (free, no key)
- News: NewsAPI (free tier, requires NEWSAPI_KEY)
- Shipping: Freightos public API (free, no key)
