"""Shared pytest fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient

from python_app.main import app
from python_app.models.schemas import (
    Claim,
    ResearchResult,
    ScoredClaim,
    SearchResult,
    TranscriptResult,
    TranscriptSource,
    VideoMetadata,
    VerdictLabel,
)


@pytest.fixture
def client(mocker) -> TestClient:
    mocker.patch("python_app.main.transcript_service.validate_runtime_dependencies")
    return TestClient(app)


@pytest.fixture
def sample_video_metadata() -> VideoMetadata:
    return VideoMetadata(
        video_id="dQw4w9WgXcQ",
        title="Rick Astley - Never Gonna Give You Up",
        channel="Rick Astley",
        published_at="2009-10-25",
        duration_seconds=212,
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )


@pytest.fixture
def sample_transcript() -> TranscriptResult:
    return TranscriptResult(
        text=(
            "Scientists have discovered that the Earth is 4.5 billion years old. "
            "According to NASA, the Moon is approximately 384,400 km from Earth. "
            "Studies show that 80 percent of the ocean remains unexplored."
        ),
        source=TranscriptSource.youtube_captions,
        language="en",
    )


@pytest.fixture
def sample_claims() -> list[Claim]:
    return [
        Claim(id="claim_1", text="The Earth is 4.5 billion years old."),
        Claim(id="claim_2", text="The Moon is approximately 384,400 km from Earth."),
    ]


@pytest.fixture
def sample_search_results() -> list[SearchResult]:
    return [
        SearchResult(
            title="Earth's Age",
            url="https://www.britannica.com/earth-age",
            snippet="Scientists confirm the Earth is approximately 4.5 billion years old.",
        ),
        SearchResult(
            title="NASA Moon Distance",
            url="https://nasa.gov/moon-distance",
            snippet="The average distance from Earth to the Moon is 384,400 km.",
        ),
    ]


@pytest.fixture
def sample_research_results(sample_claims, sample_search_results) -> list[ResearchResult]:
    return [
        ResearchResult(
            claim_id=sample_claims[0].id,
            claim_text=sample_claims[0].text,
            search_results=sample_search_results,
        ),
        ResearchResult(
            claim_id=sample_claims[1].id,
            claim_text=sample_claims[1].text,
            search_results=sample_search_results,
        ),
    ]


@pytest.fixture
def sample_scored_claims() -> list[ScoredClaim]:
    return [
        ScoredClaim(
            id="claim_1",
            text="The Earth is 4.5 billion years old.",
            verdict=VerdictLabel.supported,
            confidence=0.9,
            explanation="Multiple authoritative sources confirm this.",
            sources=["https://www.britannica.com/earth-age"],
        ),
        ScoredClaim(
            id="claim_2",
            text="The Moon is approximately 384,400 km from Earth.",
            verdict=VerdictLabel.supported,
            confidence=0.85,
            explanation="NASA data confirms this distance.",
            sources=["https://nasa.gov/moon-distance"],
        ),
    ]
