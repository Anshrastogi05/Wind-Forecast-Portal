"""Application factory. ``uvicorn windportal.main:app``."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = FastAPI(title="Wind Forecast Portal API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET"], allow_headers=["*"])
    app.include_router(router)

    if settings.static_dir and settings.static_dir.is_dir():  # single-container mode
        app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="ui")
    return app


app = create_app()
