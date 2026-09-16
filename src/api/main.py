"""FastAPI application main entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings
from src.database.connection import init_db
from src.api.routes.models import router as models_router
from src.api.routes.generate import router as generate_router
from src.api.routes.compare import router as compare_router
from src.api.routes.sessions import router as sessions_router
from src.api.routes.auth import router as auth_router
from src.api.routes.user_keys import router as user_keys_router

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("llm_judge.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing LLM-Judge platform services and database...")
    init_db()
    logger.info("LLM-Judge platform initialized successfully.")
    yield
    logger.info("Shutting down LLM-Judge platform.")


app = FastAPI(
    title="LLM-Judge Comparison & Evaluation Platform",
    description="Multi-model LLM comparison and pairwise evaluation platform using clean architecture.",
    version="2.0.0",
    lifespan=lifespan
)

import os

# CORS middleware for React / Vite frontend (supports Vercel, localhost, and custom domains)
cors_env = os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()
if cors_env:
    allowed_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Allow any HTTP / HTTPS origin (Vercel deployments, preview URLs, localhost)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
app.include_router(auth_router)
app.include_router(user_keys_router)
app.include_router(models_router)
app.include_router(generate_router)
app.include_router(compare_router)
app.include_router(sessions_router)


@app.get("/")
async def root():
    return {
        "platform": "LLM-Judge",
        "version": "2.0.0",
        "status": "operational",
        "docs_url": "/docs"
    }


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.app_env
    }
