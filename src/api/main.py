"""FastAPI application main entry point."""

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from slowapi.errors import RateLimitExceeded
from src.config.settings import settings
from src.config.database import init_db, close_db
from src.database.connection import init_db as sync_init_db
from src.api.middleware.ratelimit import limiter, rate_limit_exceeded_handler
from src.api.routes.models import router as models_router
from src.api.routes.generate import router as generate_router
from src.api.routes.compare import router as compare_router
from src.api.routes.sessions import router as sessions_router
from src.api.routes.auth import router as auth_router
from src.api.routes.user_keys import router as user_keys_router
from src.api.routes.async_evaluations import router as async_evaluations_router

# Prometheus metrics
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"])

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("llm_judge.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing LLM-Judge platform services and database...")
    try:
        sync_init_db()
    except Exception as exc:
        logger.warning(f"Sync DB init warning: {exc}")
        if settings.app_env.lower() == "production":
            raise
    try:
        await init_db()
    except Exception as exc:
        logger.warning(f"Async DB init warning: {exc}")
        if settings.app_env.lower() == "production":
            raise
    logger.info("LLM-Judge platform initialized successfully.")
    yield
    logger.info("Shutting down LLM-Judge platform.")
    try:
        await close_db()
    except Exception as exc:
        logger.warning(f"DB close warning: {exc}")


app = FastAPI(
    title="LLM-Judge Comparison & Evaluation Platform",
    description="Multi-model LLM comparison and pairwise evaluation platform using clean architecture.",
    version="2.0.0",
    lifespan=lifespan
)

from starlette.requests import Request

# CORS is restricted to explicitly configured origins. Local development
# origins are added only outside production.
allowed_origins = [
    origin.strip()
    for origin in settings.cors_allowed_origins.split(",")
    if origin.strip()
]
# The production Vercel deployment is a first-party origin and must be
# allowed even when the Render environment has not yet set this variable.
production_frontend_origin = "https://llm-as-judge-murex.vercel.app"
if production_frontend_origin not in allowed_origins:
    allowed_origins.append(production_frontend_origin)
if settings.app_env.lower() != "production":
    for origin in (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ):
        if origin not in allowed_origins:
            allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


@app.middleware("http")
async def rewrite_legacy_api_prefix(request: Request, call_next):
    """Ensure requests work whether called with /api prefix or directly."""
    path = request.url.path
    legacy_prefixes = (
        "/auth",
        "/models",
        "/generate-compare",
        "/manual-compare",
        "/sessions",
        "/user",
    )
    if any(path.startswith(p) for p in legacy_prefixes) and not path.startswith("/api"):
        request.scope["path"] = f"/api{path}"
    return await call_next(request)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Prometheus metrics middleware."""
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    latency = time.perf_counter() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(latency)
    
    return response


# Include Routers
app.include_router(auth_router)
app.include_router(user_keys_router)
app.include_router(models_router)
app.include_router(generate_router)
app.include_router(compare_router)
app.include_router(sessions_router)
app.include_router(async_evaluations_router)


@app.get("/")
async def root():
    return {
        "platform": "LLM-Judge",
        "version": "2.0.0",
        "status": "operational",
        "docs_url": "/docs"
    }


@app.get("/health")
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "version": "2.0.0"
    }


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
