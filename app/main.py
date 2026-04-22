"""
voice-agent-demo: FastAPI entrypoint.

Local run (from repository root):
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.router import router


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "voice-agent-demo"
    log_level: str = "INFO"


def _base_dir():
    from pathlib import Path

    return Path(__file__).resolve().parent


settings = Settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

app = FastAPI(
    title=settings.app_name,
    description="Post-transcript routing demo with a lightweight browser UI.",
    version="0.2.0",
)


@app.middleware("http")
async def correlation_id(request: Request, call_next):
    incoming = request.headers.get("x-request-id")
    request.state.correlation_id = incoming or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.correlation_id
    return response


app.include_router(router)
app.mount("/static", StaticFiles(directory=str(_base_dir() / "static")), name="static")
