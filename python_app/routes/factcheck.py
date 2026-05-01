"""Fact-check API routes."""

from __future__ import annotations

import json
import logging
import time

from fastapi import APIRouter, HTTPException

from python_app.config import settings
from python_app.models.schemas import FactCheckReport, FactCheckRequest
from python_app.services import (
    claim_extractor,
    report_generator,
    research_service,
    transcript_service,
    verdict_service,
)

router = APIRouter()
logger = logging.getLogger("python_app.factcheck")


def _log_event(stage: str, status: str, **fields: object) -> None:
    payload = {"stage": stage, "status": status, **fields}
    logger.info(json.dumps(payload, sort_keys=True, default=str))


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
        video = transcript_service.get_video_metadata(
            url,
            yt_dlp_timeout_seconds=settings.yt_dlp_timeout_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch video metadata: {exc}"
        ) from exc

    _log_event(
        "metadata",
        "complete",
        video_id=video.video_id,
        channel=video.channel,
        title=video.title,
    )

    # 2. Transcript
    transcript_started = time.perf_counter()
    transcript = transcript_service.get_transcript(
        url,
        whisper_model=settings.whisper_model,
        yt_dlp_timeout_seconds=settings.yt_dlp_timeout_seconds,
    )
    _log_event(
        "transcript_fetch",
        "complete",
        video_id=video.video_id,
        transcript_source=transcript.source.value,
        transcript_length=len(transcript.text),
        duration_ms=round((time.perf_counter() - transcript_started) * 1000, 2),
    )

    # 3. Claim extraction
    claim_started = time.perf_counter()
    claims = claim_extractor.extract_claims(
        transcript_text=transcript.text,
        max_claims=settings.max_claims,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
        openai_timeout_seconds=settings.openai_timeout_seconds,
    )
    _log_event(
        "claim_extraction",
        "complete",
        video_id=video.video_id,
        claim_count=len(claims),
        duration_ms=round((time.perf_counter() - claim_started) * 1000, 2),
    )

    # 4. Research
    research_started = time.perf_counter()
    research_results = research_service.research_claims(
        claims=claims,
        max_results=settings.research_max_results,
        duckduckgo_timeout_seconds=settings.duckduckgo_timeout_seconds,
    )
    research_result_count = sum(len(result.search_results) for result in research_results)
    _log_event(
        "research",
        "complete",
        video_id=video.video_id,
        claim_count=len(research_results),
        search_result_count=research_result_count,
        duration_ms=round((time.perf_counter() - research_started) * 1000, 2),
    )

    # 5. Verdict scoring
    verdict_started = time.perf_counter()
    scored_claims = verdict_service.score_claims(
        research_results=research_results,
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
        openai_timeout_seconds=settings.openai_timeout_seconds,
    )
    _log_event(
        "verdict_scoring",
        "complete",
        video_id=video.video_id,
        scored_claim_count=len(scored_claims),
        duration_ms=round((time.perf_counter() - verdict_started) * 1000, 2),
    )

    # 6. Report
    report = report_generator.generate_report(
        video=video,
        transcript_source=transcript.source,
        scored_claims=scored_claims,
    )
    _log_event(
        "report_generation",
        "complete",
        video_id=video.video_id,
        overall_credibility_score=report.overall_credibility_score,
    )

    return report
