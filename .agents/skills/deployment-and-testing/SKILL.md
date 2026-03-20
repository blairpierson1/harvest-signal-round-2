# Deployment and Testing for harvest-signal-round-2

## Architecture
- **Backend**: FastAPI app at `backend/app/main.py`, uses Poetry for dependency management
- **Frontend**: Next.js app at `frontend/`, uses static export (`output: "export"` in `next.config.ts`)

## Local Development
1. Backend: `cd backend && poetry run fastapi dev app/main.py` (runs on port 8000)
2. Frontend: `cd frontend && npm run dev` (runs on port 3000)
3. Frontend connects to backend via `NEXT_PUBLIC_API_URL` in `frontend/.env.local`

## Deployment

### Backend (Fly.io)
- Deploy using the `deploy` tool with `command: backend` and `dir: /home/ubuntu/repos/harvest-signal-round-2/backend`
- Backend URL: stored in `backend/.env` as reference
- IMPORTANT: `ALLOWED_ORIGINS` in `backend/.env` must include the deployed frontend URL for CORS
- After redeploying backend, redeploy frontend if the backend URL changes

### Frontend (Static Deploy)
- Build: `cd frontend && NEXT_PUBLIC_API_URL=<backend_url> npm run build`
- The build output is in `frontend/out/` (static export)
- Deploy using the `deploy` tool with `command: frontend` and `dir: /home/ubuntu/repos/harvest-signal-round-2/frontend/out`
- IMPORTANT: Set `NEXT_PUBLIC_API_URL` before building so API calls point to the deployed backend

## Testing the Deployed Site
1. Navigate to the deployed frontend URL
2. Wait ~10-15 seconds for initial data load (backend fetches weather, prices, news)
3. Verify all 6 commodity cards load with signal badges, prices, and key drivers
4. Verify the map shows growing region markers and shipping lane polylines
5. Click on shipping lane polylines to verify popup shows route info (commodity, origin → destination, port codes)
6. Scroll down to verify all commodity cards display shipping routes

## Key Configuration Files
- `backend/.env`: `ALLOWED_ORIGINS` (comma-separated list of allowed frontend URLs)
- `frontend/.env.local`: `NEXT_PUBLIC_API_URL` (backend API URL)
- `frontend/next.config.ts`: Must have `output: "export"` for static deployment

## Lint
- Frontend: `cd frontend && npm run lint`
- No backend linter configured

## Commodities (Middle East Focus)
Pistachios, Dates, Saffron, Cotton, Hazelnuts, Olive Oil
- Only Cotton has a Yahoo Finance ticker (CT=F); others use estimated prices
- Shipping routes connect Middle East ports (Bandar Abbas, Jeddah, Mersin, Trabzon, Izmir, Jebel Ali) to global destinations (Rotterdam, Shanghai, New York, Dubai)
