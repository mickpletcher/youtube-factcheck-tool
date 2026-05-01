"""Tests for the FastAPI routes."""

import pytest
from fastapi.testclient import TestClient

from python_app.models.schemas import (
    ScoredClaim,
    TranscriptResult,
    TranscriptSource,
    VerdictLabel,
    VideoMetadata,
)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestFactCheckEndpoint:
    def test_returns_400_for_non_youtube_url(self, client):
        response = client.post("/factcheck", json={"url": "https://vimeo.com/123456"})
        assert response.status_code == 422  # Pydantic validation error

    def test_returns_422_for_oversized_url(self, client):
        long_query = "a" * 2100
        response = client.post(
            "/factcheck",
            json={"url": f"https://www.youtube.com/watch?v=dQw4w9WgXcQ&x={long_query}"},
        )
        assert response.status_code == 422

    def test_returns_full_report(self, client, mocker, sample_video_metadata, sample_scored_claims):
        """Full pipeline mock – ensures the route correctly wires all services."""
        mocker.patch(
            "python_app.routes.factcheck.transcript_service.get_video_metadata",
            return_value=sample_video_metadata,
        )
        mocker.patch(
            "python_app.routes.factcheck.transcript_service.get_transcript",
            return_value=TranscriptResult(
                text="Scientists discovered Earth is 4.5 billion years old.",
                source=TranscriptSource.youtube_captions,
                language="en",
            ),
        )
        mocker.patch(
            "python_app.routes.factcheck.claim_extractor.extract_claims",
            return_value=[],
        )
        mocker.patch(
            "python_app.routes.factcheck.research_service.research_claims",
            return_value=[],
        )
        mocker.patch(
            "python_app.routes.factcheck.verdict_service.score_claims",
            return_value=sample_scored_claims,
        )

        response = client.post(
            "/factcheck",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "video" in data
        assert "claims" in data
        assert "summary" in data
        assert "overall_credibility_score" in data
        assert "report_markdown" in data
        assert data["video"]["video_id"] == "dQw4w9WgXcQ"

    def test_returns_502_on_metadata_error(self, client, mocker):
        mocker.patch(
            "python_app.routes.factcheck.transcript_service.get_video_metadata",
            side_effect=RuntimeError("Network unreachable"),
        )
        response = client.post(
            "/factcheck",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 502

    def test_report_markdown_in_response(self, client, mocker, sample_video_metadata):
        mocker.patch(
            "python_app.routes.factcheck.transcript_service.get_video_metadata",
            return_value=sample_video_metadata,
        )
        mocker.patch(
            "python_app.routes.factcheck.transcript_service.get_transcript",
            return_value=TranscriptResult(
                text="",
                source=TranscriptSource.unavailable,
            ),
        )
        mocker.patch(
            "python_app.routes.factcheck.claim_extractor.extract_claims",
            return_value=[],
        )
        mocker.patch(
            "python_app.routes.factcheck.research_service.research_claims",
            return_value=[],
        )
        mocker.patch(
            "python_app.routes.factcheck.verdict_service.score_claims",
            return_value=[],
        )

        response = client.post(
            "/factcheck",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "# Fact-Check Report" in data["report_markdown"]
        assert data["transcript_source"] == TranscriptSource.unavailable.value

    def test_openapi_docs_available(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_available(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/factcheck" in schema["paths"]
        assert "/health" in schema["paths"]
