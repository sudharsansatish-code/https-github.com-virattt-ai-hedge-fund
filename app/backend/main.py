import os
import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

from app.backend.routes import api_router
from app.backend.database.connection import engine
from app.backend.database.models import Base
from app.backend.services.ollama_service import ollama_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Hedge Fund API", description="Backend API for AI Hedge Fund", version="1.0.0")

# Initialize database tables (this is safe to run multiple times)
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # HSTS only when served over HTTPS (Render provides HTTPS automatically)
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ---------------------------------------------------------------------------
# Bearer Token Authentication Middleware
# ---------------------------------------------------------------------------

# When API_AUTH_TOKEN is set, all non-public endpoints require
# Authorization: Bearer <token>.  When unset, auth is disabled (local dev).
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "")

# Paths that are always publicly accessible (no auth required)
# NOTE: paths must match actual routes (no /api prefix — routes have no global prefix).
# The root path "/" is handled separately via `path == ""` after rstrip("/").
PUBLIC_PATHS = {"/health", "/ping", "/docs", "/openapi.json", "/redoc"}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Optional bearer-token authentication gated by API_AUTH_TOKEN env var."""

    async def dispatch(self, request: Request, call_next):
        if not API_AUTH_TOKEN:
            # Auth disabled — allow all requests (local dev)
            return await call_next(request)

        path = request.url.path.rstrip("/")

        # Allow public paths
        if path in PUBLIC_PATHS or path == "":
            return await call_next(request)

        # Allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header == f"Bearer {API_AUTH_TOKEN}":
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized — provide a valid API_AUTH_TOKEN"},
        )


app.add_middleware(BearerAuthMiddleware)


# ---------------------------------------------------------------------------
# CORS Configuration (from environment variable)
# ---------------------------------------------------------------------------

ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware

    limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    logger.info("Rate limiting enabled (slowapi)")
except ImportError:
    logger.warning("slowapi not installed — rate limiting disabled. Install with: pip install slowapi")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(api_router)


# ---------------------------------------------------------------------------
# Startup Event
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """Startup event to check Ollama availability."""
    logger.info(f"CORS allowed origins: {ALLOWED_ORIGINS}")
    logger.info(f"Auth enabled: {bool(API_AUTH_TOKEN)}")

    try:
        logger.info("Checking Ollama availability...")
        status = await ollama_service.check_ollama_status()

        if status["installed"]:
            if status["running"]:
                logger.info(f"Ollama is installed and running at {status['server_url']}")
                if status["available_models"]:
                    logger.info(f"Available models: {', '.join(status['available_models'])}")
                else:
                    logger.info("No models are currently downloaded")
            else:
                logger.info("Ollama is installed but not running")
        else:
            logger.info("Ollama is not installed. Install it to use local models.")

    except Exception as e:
        logger.warning(f"Could not check Ollama status: {e}")
        logger.info("Ollama integration is available if you install it later")
