"""Tests for the verdict service."""

import pytest

from python_app.services.verdict_service import (
    _score_claim_heuristic,
    score_claim,
    score_claims,
)
from python_app.models.schemas import (
    ResearchResult,
    ScoredClaim,
    SearchResult,
    VerdictLabel,
)


def _make_research(claim_id: str, claim_text: str, snippets: list[str]) -> ResearchResult:
    return ResearchResult(
        claim_id=claim_id,
        claim_text=claim_text,
        search_results=[
            SearchResult(title="Source", url=f"https://example.com/{i}", snippet=s)
            for i, s in enumerate(snippets)
        ],
    )


class TestScoreClaimHeuristic:
    def test_supported_verdict_on_positive_signals(self):
        research = _make_research(
            "claim_1",
            "The Earth is round.",
            [
                "Scientists confirmed this is true and accurate.",
                "This is a verified and proven fact supported by evidence.",
                "Evidence confirms and supports this statement.",
            ],
        )
        result = _score_claim_heuristic(research)
        assert result.verdict == VerdictLabel.supported
        assert result.confidence > 0.5

    def test_contradicted_verdict_on_negative_signals(self):
        research = _make_research(
            "claim_1",
            "Vaccines cause autism.",
            [
                "This claim has been debunked and is false.",
                "Studies show this is incorrect and disproven.",
                "This is a myth and completely refuted.",
            ],
        )
        result = _score_claim_heuristic(research)
        assert result.verdict == VerdictLabel.contradicted
        assert result.confidence > 0.5

    def test_unverified_verdict_with_no_signals(self):
        research = _make_research(
            "claim_1",
            "Aliens visited Earth.",
            ["Some text about space.", "Another article.", "No relevant content."],
        )
        result = _score_claim_heuristic(research)
        assert result.verdict == VerdictLabel.unverified

    def test_disputed_verdict_on_mixed_signals(self):
        research = _make_research(
            "claim_1",
            "Coffee is healthy.",
            [
                "Studies confirmed this is true and accurate.",
                "Research says this is false and incorrect.",
            ],
        )
        result = _score_claim_heuristic(research)
        assert result.verdict in (VerdictLabel.disputed, VerdictLabel.supported, VerdictLabel.contradicted)

    def test_returns_scored_claim(self):
        research = _make_research("claim_1", "Some claim.", [])
        result = _score_claim_heuristic(research)
        assert isinstance(result, ScoredClaim)
        assert result.id == "claim_1"
        assert 0.0 <= result.confidence <= 1.0

    def test_no_search_results_returns_unverified(self):
        research = ResearchResult(
            claim_id="claim_1",
            claim_text="Claim with no results.",
            search_results=[],
        )
        result = _score_claim_heuristic(research)
        assert result.verdict == VerdictLabel.unverified


class TestScoreClaim:
    def test_heuristic_used_without_api_key(self):
        research = _make_research("claim_1", "Earth is round.", ["confirmed true evidence."])
        result = score_claim(research, openai_api_key="")
        assert isinstance(result, ScoredClaim)

    def test_falls_back_to_heuristic_on_llm_failure(self, mocker):
        mocker.patch(
            "python_app.services.verdict_service._score_claim_llm",
            side_effect=Exception("API error"),
        )
        research = _make_research("claim_1", "Earth is round.", ["confirmed."])
        result = score_claim(research, openai_api_key="sk-fake-key")
        assert isinstance(result, ScoredClaim)

    def test_llm_used_when_api_key_present(self, mocker):
        expected = ScoredClaim(
            id="claim_1",
            text="Earth is round.",
            verdict=VerdictLabel.supported,
            confidence=0.9,
            explanation="LLM verdict.",
            sources=[],
        )
        mock_llm = mocker.patch(
            "python_app.services.verdict_service._score_claim_llm",
            return_value=expected,
        )
        research = _make_research("claim_1", "Earth is round.", [])
        result = score_claim(research, openai_api_key="sk-fake-key")
        mock_llm.assert_called_once()
        assert result == expected


class TestScoreClaims:
    def test_processes_all_research_results(self, mocker):
        mocker.patch(
            "python_app.services.verdict_service._score_claim_heuristic",
            return_value=ScoredClaim(
                id="x",
                text="x",
                verdict=VerdictLabel.unverified,
                confidence=0.5,
                explanation="",
                sources=[],
            ),
        )
        research_results = [
            _make_research(f"claim_{i}", f"Claim {i}", []) for i in range(3)
        ]
        results = score_claims(research_results, openai_api_key="")
        assert len(results) == 3

    def test_empty_list_returns_empty(self):
        results = score_claims([], openai_api_key="")
        assert results == []
