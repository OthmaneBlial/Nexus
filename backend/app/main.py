from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.reports import router as reports_router
from .api.routes import router as api_router
from .api.users import router as users_router
from .db import init_db

app = FastAPI(title="Nexus API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(users_router)
app.include_router(reports_router)


def mount_frontend() -> None:
    """Mount the static frontend directory if it exists."""
    frontend_dir = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    mount_frontend()


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Lightweight health check for service readiness."""
    return {"status": "ok"}
