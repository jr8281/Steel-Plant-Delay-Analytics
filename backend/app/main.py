from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.routers import analytics, assistant, auth, delays, predictions, upload

configure_logging()

app = FastAPI(
    title="Steel Plant Delay Analytics API",
    version="1.1.0",
    description=(
        "Enterprise operational analytics platform for steel plant equipment delays. "
        "Provides role-based dashboards, delay-duration risk prediction, and AI-powered Q&A."
    ),
    contact={
        "name": "API Support",
        "email": "support@steelplant.local"
    },
)

# Security: Trust only specific hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[host.strip() for host in settings.allowed_hosts.split(",")]
)

# CORS: Allow only configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    return response

app.include_router(auth.router, tags=["Authentication"])
app.include_router(delays.router, tags=["Delays"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(assistant.router, tags=["AI Assistant"])
app.include_router(upload.router, tags=["Data Management"])
app.include_router(predictions.router, tags=["ML Predictions"])


@app.get(
    "/health",
    summary="Service Health Check",
    description="Check if the API is running and database is accessible.",
    tags=["System"],
    response_model=dict
)
def health():
    """
    Health check endpoint for load balancers and orchestration.
    
    Returns:
        - `status`: "ok" if service is healthy
        - `timestamp`: Current server timestamp in ISO format
        - `service`: Service name
    """
    from datetime import datetime
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Steel Plant Delay Analytics API"
    }