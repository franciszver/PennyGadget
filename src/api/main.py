"""
FastAPI Application
Main entry point for AI Study Companion API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import logging

from src.config.settings import settings
from src.config.database import engine, check_database_connection
from src.models.base import Base
from src.api.middleware.error_handlers import (
    validation_exception_handler,
    database_exception_handler,
    general_exception_handler
)
from src.api.middleware.request_logging import RequestLoggingMiddleware
from src.api.middleware.metrics import MetricsMiddleware
from src.utils.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Study Companion API...")
    
    # Setup logging
    setup_logging()
    
    # Store environment in app state for error handling
    app.state.environment = settings.environment
    
    # Verify database connection
    if not check_database_connection():
        logger.error("Database connection failed on startup")
        raise RuntimeError("Database connection failed on startup")
    logger.info("Database connection verified")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Study Companion API...")


# Create FastAPI app
app = FastAPI(
    title="AI Study Companion API",
    description="Persistent AI agent supporting students between tutoring sessions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Request logging middleware
if settings.environment == "development":
    app.add_middleware(RequestLoggingMiddleware)

# Metrics middleware (always enabled)
app.add_middleware(MetricsMiddleware)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Study Companion API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = check_database_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }


@app.get("/metrics")
async def get_metrics():
    """
    Get application metrics
    
    Note: In production, protect this endpoint with authentication
    """
    from src.utils.metrics import get_metrics
    
    metrics = get_metrics()
    return {
        "success": True,
        "data": metrics.get_all_metrics()
    }


# Import routers
from src.api.handlers import summaries, practice, qa, progress, nudges, overrides, messaging, dashboards, advanced_analytics, integrations, enhancements, goals

app.include_router(summaries.router, prefix="/api/v1")
app.include_router(practice.router, prefix="/api/v1")
app.include_router(qa.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(nudges.router, prefix="/api/v1")
app.include_router(overrides.router, prefix="/api/v1")
app.include_router(messaging.router, prefix="/api/v1")
app.include_router(dashboards.router, prefix="/api/v1")
app.include_router(advanced_analytics.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")
app.include_router(enhancements.router, prefix="/api/v1")
app.include_router(goals.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )

