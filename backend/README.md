# Harvest Signal Backend

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `API_KEY` | Yes (prod) | Secret key used to authenticate requests via `X-API-Key` header or `Authorization: Bearer` token. Must be set in production. |
| `DISABLE_AUTH` | No | Set to `true` to skip API key authentication. **For local development only.** |
| `TRUSTED_PROXY` | No | Set to `true` when running behind a reverse proxy (e.g., Fly.io) so rate limiting uses the real client IP from `X-Forwarded-For`. |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins. Defaults to `http://localhost:3000`. |
| `NEWSAPI_KEY` | No | NewsAPI.org key for fetching commodity news headlines. News fetch is skipped if absent. |

### Local Development

```bash
# Create a .env file for local development
echo 'DISABLE_AUTH=true' > .env

# Or set a real API key
echo 'API_KEY=your-secret-key-here' > .env

# Start the backend
poetry install
poetry run fastapi dev app/main.py
```

When `DISABLE_AUTH=true` is set, authentication is completely bypassed. When it is not set, `API_KEY` **must** be configured or all requests will return a 500 error.
