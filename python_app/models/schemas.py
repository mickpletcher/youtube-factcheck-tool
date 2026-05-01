"""Pydantic schemas for the YouTube Fact-Check Tool."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, HttpUrl, field_validator


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------


class FactCheckRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        if "youtube.com" not in v and "youtu.be" not in v:
            raise ValueError("URL must be a YouTube link (youtube.com or youtu.be)")
        return v


# ---------------------------------------------------------------------------
# Video metadata
# ---------------------------------------------------------------------------


class VideoMetadata(BaseModel):
    video_id: str
    title: str
    channel: str
    published_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    url: str


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------


class TranscriptSource(str, Enum):
    youtube_captions = "youtube_captions"
    audio_transcription = "audio_transcription"
    unavailable = "unavailable"


class TranscriptResult(BaseModel):
    text: str
    source: TranscriptSource
    language: Optional[str] = None


# ---------------------------------------------------------------------------
# Claims
# ---------------------------------------------------------------------------


class Claim(BaseModel):
    id: str
    text: str


# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class ResearchResult(BaseModel):
    claim_id: str
    claim_text: str
    search_results: List[SearchResult] = []


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


class VerdictLabel(str, Enum):
    supported = "Supported"
    contradicted = "Contradicted"
    unverified = "Unverified"
    disputed = "Disputed"


class ScoredClaim(BaseModel):
    id: str
    text: str
    verdict: VerdictLabel
    confidence: float  # 0.0 – 1.0
    explanation: str
    sources: List[str] = []


# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------


class FactCheckReport(BaseModel):
    video: VideoMetadata
    transcript_source: TranscriptSource
    claims: List[ScoredClaim] = []
    summary: str
    overall_credibility_score: float  # 0.0 – 1.0
    report_markdown: str
