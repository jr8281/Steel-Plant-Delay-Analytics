from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import analytics, assistant, auth, delays, upload

app = FastAPI(title="Steel Plant Delay Analytics API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(delays.router)
app.include_router(analytics.router)
app.include_router(assistant.router)
app.include_router(upload.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
