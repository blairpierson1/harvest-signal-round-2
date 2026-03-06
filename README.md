# Harvest Signal

Middle East commodity weather signal dashboard that shows daily price direction signals (Bullish / Bearish / Neutral) for five commodities based on real-time weather data from growing regions across the Middle East.

**Live Dashboard**: https://soft-commodity-dashboard-ao789btn.devinapps.com
**Backend API**: https://harvest-signal-backend-eyzjavel.fly.dev/api/signals

## What It Does

Harvest Signal monitors weather conditions across major Middle East commodity-producing regions and generates trading signals based on supply risk analysis. Each commodity card displays a signal badge, key weather driver, confidence level, live price, 30-day sparkline chart, price forecast direction, top producing countries with weather risk badges, and latest news headlines.

### Commodities Tracked

| Commodity | Ticker | Growing Regions | Top Producers |
|-----------|--------|-----------------|---------------|
| Pistachios | — (estimated) | Iran (Kerman), Turkey (Gaziantep), Syria (Aleppo) | Iran, Turkey, Saudi Arabia, Lebanon, Jordan |
| Figs | — (estimated) | Turkey (Aydin), Iran (Fars), Lebanon (Bekaa Valley) | Turkey, Iran, Saudi Arabia, Iraq, Lebanon |
| Olives | — (estimated) | Turkey (Aegean), Israel (Northern), Jordan (Ajloun) | Turkey, Israel, Jordan, Lebanon, Iraq |
| Dates | — (estimated) | Saudi Arabia (Al-Ahsa), Iraq (Basra), Iran (Khuzestan) | Saudi Arabia, Iraq, Iran, Israel, Jordan |
| Citrus | OJ=F | Turkey (Mediterranean Coast), Israel (Coastal Plain), Lebanon (Bekaa Valley) | Turkey, Iran, Israel, Lebanon, Iraq |

## Signal Logic

Weather data is fetched from Open-Meteo for each commodity's growing regions using a 7-day rolling window. Anomaly scores are computed for drought, flood, and heat stress:

- **Drought**: Low precipitation + high temperatures + low humidity
- **Flood**: Excessive precipitation
- **Heat stress**: Sustained high maximum temperatures

These scores drive the signal:

| Condition | Signal | Color |
|-----------|--------|-------|
| Drought >= 5, or drought >= 3 + heat >= 2, or heat >= 4 | **Bullish** | Green |
| Flood >= 4 | **Bearish** | Red |
| Otherwise | **Neutral** | Amber |

Country-level weather alerts from top producing countries can also elevate a Neutral signal to Bullish when major producers (covering >= 15% of regional output or >= 2 countries at Alert status) show adverse conditions.

**Price forecast direction** combines the weather signal with the 30-day price trend:
- Bullish + Downtrend = "Potential Reversal Upward"
- Bullish + Uptrend = "Momentum Confirmed Upward"
- Bearish + Uptrend = "Potential Reversal Downward"
- Neutral = "No Clear Directional Bias"

## Tech Stack

### Backend
- **Python 3.11+** with **FastAPI**
- **Open-Meteo API** for weather data (free, no key needed)
- **Yahoo Finance** for commodity futures prices (Citrus/OJ=F; others use estimated fallback)
- **NewsAPI** for commodity news headlines (requires API key)
- **httpx** for async HTTP requests
- **Pydantic** for data models
- All API calls parallelized via `asyncio.gather()`

### Frontend
- **Next.js 16** (static export)
- **React 19**
- **Tailwind CSS v4**
- **Recharts** for 30-day sparkline charts
- **TypeScript**
- Dark Bloomberg-terminal aesthetic with responsive grid

## Running Locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Poetry](https://python-poetry.org/) for Python dependency management

### Backend

```bash
cd backend

# Install dependencies
poetry install

# (Optional) Create .env file for API keys and configuration
cat > .env << EOF
NEWSAPI_KEY=your_newsapi_key_here
ALLOWED_ORIGINS=http://localhost:3000
API_KEY=
EOF

# Start the development server
poetry run fastapi dev app/main.py
```

The backend runs at `http://localhost:8000`. Weather data works without any API keys. Most commodity prices use estimated fallback values since Middle East commodities lack liquid Yahoo Finance futures tickers. The news section requires a `NEWSAPI_KEY` from [newsapi.org](https://newsapi.org/) (free tier: 100 requests/day).

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Point to your local backend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start the development server
npm run dev
```

The frontend runs at `http://localhost:3000`.

### Building for Production

```bash
cd frontend
npm run build
```

Produces a static export in `frontend/out/` deployable to any static hosting provider.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEWSAPI_KEY` | Optional | [NewsAPI.org](https://newsapi.org/) key for news headlines. Without it, the news section is empty. |
| `ALLOWED_ORIGINS` | Optional | Comma-separated list of allowed CORS origins. Defaults to `http://localhost:3000`. |
| `API_KEY` | Optional | API key for authenticating requests to `/api/signals`. If not set, authentication is disabled (convenient for local dev). Clients pass the key via `X-API-Key` header or `Authorization: Bearer <key>`. |
| `NEXT_PUBLIC_API_URL` | Required (frontend) | Backend API URL. Defaults to `http://localhost:8000`. |

## Project Structure

```
harvest-signal-round-2/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app with CORS
│   │   ├── routes.py        # /api/signals endpoint
│   │   ├── models.py        # Pydantic data models
│   │   ├── weather.py       # Open-Meteo API integration
│   │   ├── prices.py        # Yahoo Finance + estimated fallback
│   │   ├── signals.py       # Signal generation logic
│   │   ├── forecast.py      # Price forecast direction
│   │   ├── producers.py     # Top producing countries + weather
│   │   ├── news.py          # NewsAPI integration
│   │   └── shipping.py      # Freightos shipping rate integration
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   │   ├── components/      # React components
│   │   ├── types.ts         # TypeScript interfaces
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Main page
│   ├── next.config.ts
│   └── package.json
└── README.md
```
