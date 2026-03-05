from dotenv import load_dotenv

load_dotenv()  # Load .env file before anything else reads os.environ

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.dependencies import ALLOWED_ORIGINS, limiter, log_startup_warnings
from app.routes import router

app = FastAPI(title="Harvest Signal API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)

log_startup_warnings()
