"""Fact-check API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import FactCheckReport, FactCheckRequest
from app.services import (
    claim_extractor,
    report_generator,
    research_service,
    transcript_service,
    verdict_service,
)

router = APIRouter()


@router.post("/factcheck", response_model=FactCheckReport, summary="Fact-check a YouTube video")
async def factcheck(request: FactCheckRequest) -> FactCheckReport:
    """Accept a YouTube URL and return a full fact-check report.

    The pipeline:
    1. Extract video metadata.
    2. Fetch transcript (captions → audio transcription fallback).
    3. Extract factual claims from the transcript.
    4. Research each claim via web search.
    5. Score each claim's validity.
    6. Generate and return a JSON + Markdown report.
    """
    url = request.url

    # 1. Metadata
    try:
        video = transcript_service.get_video_metadata(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch video metadata: {exc}"
        ) from exc

    # 2. Transcript
    transcript = transcript_service.get_transcript(url, whisper_model=settings.whisper_model)

    # 3. Claim extraction
    claims = claim_extractor.extract_claims(
        transcript_text=transcript.text,
        max_claims=settings.max_claims,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
    )

    # 4. Research
    research_results = research_service.research_claims(
        claims=claims,
        max_results=settings.research_max_results,
    )

    # 5. Verdict scoring
    scored_claims = verdict_service.score_claims(
        research_results=research_results,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
    )

    # 6. Report
    report = report_generator.generate_report(
        video=video,
        transcript_source=transcript.source,
        scored_claims=scored_claims,
    )

    return report
