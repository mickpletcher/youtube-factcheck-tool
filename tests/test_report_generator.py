"""Tests for the report generator service."""

import pytest

from app.services.report_generator import (
    _compute_overall_score,
    _build_summary,
    _generate_markdown,
    generate_report,
)
from app.models.schemas import (
    FactCheckReport,
    ScoredClaim,
    TranscriptSource,
    VerdictLabel,
    VideoMetadata,
)


def _make_claim(
    id: str,
    verdict: VerdictLabel,
    confidence: float,
    text: str = "A factual claim.",
) -> ScoredClaim:
    return ScoredClaim(
        id=id,
        text=text,
        verdict=verdict,
        confidence=confidence,
        explanation="Some explanation.",
        sources=["https://example.com"],
    )


class TestComputeOverallScore:
    def test_all_supported_returns_high_score(self):
        claims = [
            _make_claim("c1", VerdictLabel.supported, 0.9),
            _make_claim("c2", VerdictLabel.supported, 0.8),
        ]
        score = _compute_overall_score(claims)
        assert score > 0.8

    def test_all_contradicted_returns_zero(self):
        claims = [
            _make_claim("c1", VerdictLabel.contradicted, 0.9),
            _make_claim("c2", VerdictLabel.contradicted, 0.8),
        ]
        score = _compute_overall_score(claims)
        assert score == 0.0

    def test_empty_claims_returns_neutral(self):
        assert _compute_overall_score([]) == 0.5

    def test_mixed_verdicts_returns_intermediate_score(self):
        claims = [
            _make_claim("c1", VerdictLabel.supported, 0.9),
            _make_claim("c2", VerdictLabel.contradicted, 0.9),
        ]
        score = _compute_overall_score(claims)
        assert 0.0 < score < 1.0

    def test_score_is_between_zero_and_one(self):
        claims = [
            _make_claim("c1", VerdictLabel.disputed, 0.6),
            _make_claim("c2", VerdictLabel.unverified, 0.5),
        ]
        score = _compute_overall_score(claims)
        assert 0.0 <= score <= 1.0


class TestBuildSummary:
    def test_no_claims_returns_special_message(self):
        summary = _build_summary([], 0.5)
        assert "No factual claims" in summary

    def test_summary_contains_claim_count(self):
        claims = [_make_claim("c1", VerdictLabel.supported, 0.9)]
        summary = _build_summary(claims, 0.9)
        assert "1" in summary

    def test_high_score_credible_assessment(self):
        claims = [_make_claim("c1", VerdictLabel.supported, 0.9)]
        summary = _build_summary(claims, 0.85)
        assert "credible" in summary.lower()

    def test_low_score_inaccurate_assessment(self):
        claims = [_make_claim("c1", VerdictLabel.contradicted, 0.9)]
        summary = _build_summary(claims, 0.1)
        assert "inaccurate" in summary.lower() or "contradicted" in summary.lower() or "largely" in summary.lower()


class TestGenerateMarkdown:
    def test_contains_video_title(self, sample_video_metadata):
        md = _generate_markdown(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.youtube_captions,
            claims=[],
            summary="No claims.",
            overall_score=0.5,
        )
        assert sample_video_metadata.title in md

    def test_contains_report_header(self, sample_video_metadata):
        md = _generate_markdown(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.youtube_captions,
            claims=[],
            summary="No claims.",
            overall_score=0.5,
        )
        assert "# Fact-Check Report" in md

    def test_contains_claim_text(self, sample_video_metadata):
        claims = [_make_claim("claim_1", VerdictLabel.supported, 0.9, "Earth is round.")]
        md = _generate_markdown(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.youtube_captions,
            claims=claims,
            summary="1 claim analysed.",
            overall_score=0.9,
        )
        assert "Earth is round." in md

    def test_contains_verdict_emoji(self, sample_video_metadata):
        claims = [_make_claim("claim_1", VerdictLabel.supported, 0.9)]
        md = _generate_markdown(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.youtube_captions,
            claims=claims,
            summary="Summary.",
            overall_score=0.9,
        )
        assert "✅" in md

    def test_contradicted_emoji(self, sample_video_metadata):
        claims = [_make_claim("claim_1", VerdictLabel.contradicted, 0.9)]
        md = _generate_markdown(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.youtube_captions,
            claims=claims,
            summary="Summary.",
            overall_score=0.0,
        )
        assert "❌" in md


class TestGenerateReport:
    def test_returns_fact_check_report(self, sample_video_metadata, sample_scored_claims):
        report = generate_report(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.youtube_captions,
            scored_claims=sample_scored_claims,
        )
        assert isinstance(report, FactCheckReport)

    def test_report_markdown_is_non_empty(self, sample_video_metadata, sample_scored_claims):
        report = generate_report(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.youtube_captions,
            scored_claims=sample_scored_claims,
        )
        assert len(report.report_markdown) > 0

    def test_report_contains_claims(self, sample_video_metadata, sample_scored_claims):
        report = generate_report(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.youtube_captions,
            scored_claims=sample_scored_claims,
        )
        assert len(report.claims) == len(sample_scored_claims)

    def test_overall_score_is_between_zero_and_one(self, sample_video_metadata, sample_scored_claims):
        report = generate_report(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.youtube_captions,
            scored_claims=sample_scored_claims,
        )
        assert 0.0 <= report.overall_credibility_score <= 1.0

    def test_no_claims_report(self, sample_video_metadata):
        report = generate_report(
            video=sample_video_metadata,
            transcript_source=TranscriptSource.unavailable,
            scored_claims=[],
        )
        assert report.overall_credibility_score == 0.5
        assert report.claims == []
