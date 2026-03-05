# Harvest Signal

Soft commodity weather signal dashboard that shows daily price direction signals (Bullish / Bearish / Neutral) for six commodities based on real-time weather data from growing regions worldwide.

**Live Dashboard**: https://soft-commodity-dashboard-ao789btn.devinapps.com
**Backend API**: https://harvest-signal-backend-eyzjavel.fly.dev/api/signals

## What It Does

Harvest Signal monitors weather conditions across major commodity-producing regions and generates trading signals based on supply risk analysis. Each commodity card displays a signal badge, key weather driver, confidence level, live price, 30-day sparkline chart, price forecast direction, top producing countries with weather risk badges, and latest news headlines.

### Commodities Tracked

| Commodity | Ticker | Growing Regions | Top Producers |
|-----------|--------|-----------------|---------------|
| Pistachios | N/A (estimated) | Kerman (Iran), Gaziantep (Turkey), San Joaquin Valley (USA) | Iran, USA, Turkey, China, Syria |
| Dates | N/A (estimated) | Medina (Saudi Arabia), Basra (Iraq), Siwa (Egypt) | Egypt, Saudi Arabia, Iran, Algeria, Iraq |
| Saffron | N/A (estimated) | Khorasan (Iran), Herat (Afghanistan), Kashmir (India) | Iran, India, Afghanistan, Spain, Morocco |
| Cotton | CT=F | SE Anatolia (Turkey), Nile Delta (Egypt), Sindh (Pakistan) | Turkey, Egypt, Pakistan, India, Uzbekistan |
| Hazelnuts | N/A (estimated) | Black Sea (Turkey), Piemonte (Italy), Sheki (Azerbaijan) | Turkey, Italy, Azerbaijan, USA, Georgia |
| Olive Oil | N/A (estimated) | Aegean (Turkey), Sfax (Tunisia), Latakia (Syria) | Turkey, Tunisia, Syria, Morocco, Jordan |

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

Country-level weather alerts from top producing countries can also elevate a Neutral signal to Bullish when major producers (covering >= 15% of global output or >= 2 countries at Alert status) show adverse conditions.

**Price forecast direction** combines the weather signal with the 30-day price trend:
- Bullish + Downtrend = "Potential Reversal Upward"
- Bullish + Uptrend = "Momentum Confirmed Upward"
- Bearish + Uptrend = "Potential Reversal Downward"
- Neutral = "No Clear Directional Bias"

## Tech Stack

### Backend
- **Python 3.11+** with **FastAPI**
- **Open-Meteo API** for weather data (free, no key needed)
- **Yahoo Finance** for commodity futures prices (primary source)
- **Alpha Vantage** as last-resort fallback for Coffee pricing
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
- Dark Bloomberg-terminal aesthetic with 2x3 responsive grid

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
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
ALLOWED_ORIGINS=http://localhost:3000
API_KEY=
EOF

# Start the development server
poetry run fastapi dev app/main.py
```

The backend runs at `http://localhost:8000`. Weather data and Yahoo Finance prices work without any API keys. The news section requires a `NEWSAPI_KEY` from [newsapi.org](https://newsapi.org/) (free tier: 100 requests/day).

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
| `ALPHA_VANTAGE_API_KEY` | Optional | [Alpha Vantage](https://www.alphavantage.co/) key, last-resort fallback for Coffee pricing only. |
| `ALLOWED_ORIGINS` | Optional | Comma-separated list of allowed CORS origins. Defaults to `http://localhost:3000`. |
| `API_KEY` | Optional | API key for authenticating requests to `/api/signals`. If not set, authentication is disabled (convenient for local dev). Clients pass the key via `X-API-Key` header or `Authorization: Bearer <key>`. |
| `NEXT_PUBLIC_API_URL` | Required (frontend) | Backend API URL. Defaults to `http://localhost:8000`. |

## Project Structure

```
harvest-signal/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app with CORS
│   │   ├── routes.py        # /api/signals endpoint
│   │   ├── models.py        # Pydantic data models
│   │   ├── weather.py       # Open-Meteo API integration
│   │   ├── prices.py        # Yahoo Finance + Alpha Vantage
│   │   ├── signals.py       # Signal generation logic
│   │   ├── forecast.py      # Price forecast direction
│   │   ├── producers.py     # Top producing countries + weather
│   │   └── news.py          # NewsAPI integration
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   │   ├── components/      # React components
│   │   ├── types.ts         # TypeScript interfaces
│   │   ├── layout.tsx        # Root layout
│   │   └── page.tsx          # Main page
│   ├── next.config.ts
│   └── package.json
└── README.md
```
