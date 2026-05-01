"""FastAPI application entry point."""

from fastapi import FastAPI

from python_app.routes.factcheck import router as factcheck_router

app = FastAPI(
    title="YouTube Fact-Check Tool",
    description=(
        "Accepts a YouTube URL, extracts the transcript, identifies factual claims, "
        "researches them against trusted sources, scores their validity, and returns "
        "a credibility report in JSON and Markdown."
    ),
    version="1.0.0",
)

app.include_router(factcheck_router)


@app.get("/health", summary="Health check")
async def health() -> dict:
    """Return a simple liveness probe response."""
    return {"status": "ok"}
