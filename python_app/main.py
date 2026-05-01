"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from python_app.routes.factcheck import router as factcheck_router
from python_app.services import transcript_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    transcript_service.validate_runtime_dependencies()
    yield

app = FastAPI(
    title="YouTube Fact-Check Tool",
    description=(
        "Accepts a YouTube URL, extracts the transcript, identifies factual claims, "
        "researches them against trusted sources, scores their validity, and returns "
        "a credibility report in JSON and Markdown."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(factcheck_router)


@app.get("/health", summary="Health check")
async def health() -> dict:
    """Return a simple liveness probe response."""
    return {"status": "ok"}
