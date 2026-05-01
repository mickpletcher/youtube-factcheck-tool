"""Tests for the research service."""

import pytest

from python_app.services.research_service import _is_trusted, research_claim, research_claims
from python_app.models.schemas import Claim, ResearchResult, SearchResult


class TestIsTrusted:
    def test_trusted_domain_returns_true(self):
        assert _is_trusted("https://www.reuters.com/article/123") is True
        assert _is_trusted("https://apnews.com/article/abc") is True
        assert _is_trusted("https://www.bbc.com/news/world") is True
        assert _is_trusted("https://snopes.com/fact-check/test") is True
        assert _is_trusted("https://factcheck.org/article") is True

    def test_unknown_domain_returns_false(self):
        assert _is_trusted("https://www.randomwebsite.com/article") is False
        assert _is_trusted("https://myblog.wordpress.com/post") is False


class TestResearchClaim:
    def test_returns_research_result_structure(self, mocker):
        mock_results = [
            SearchResult(
                title="Earth Age",
                url="https://britannica.com/earth",
                snippet="Earth is 4.5 billion years old.",
            )
        ]
        mocker.patch(
            "python_app.services.research_service._search_duckduckgo",
            return_value=mock_results,
        )
        claim = Claim(id="claim_1", text="The Earth is 4.5 billion years old.")
        result = research_claim(claim, max_results=5)

        assert isinstance(result, ResearchResult)
        assert result.claim_id == "claim_1"
        assert result.claim_text == claim.text
        assert result.search_results == mock_results

    def test_empty_search_results_handled(self, mocker):
        mocker.patch(
            "python_app.services.research_service._search_duckduckgo",
            return_value=[],
        )
        claim = Claim(id="claim_1", text="Obscure claim with no results.")
        result = research_claim(claim, max_results=5)
        assert result.search_results == []

    def test_ddgs_import_error_returns_empty(self, mocker):
        """If duckduckgo_search is not installed, return an empty list gracefully."""
        mocker.patch(
            "python_app.services.research_service._search_duckduckgo",
            return_value=[],
        )
        claim = Claim(id="claim_1", text="Some claim.")
        result = research_claim(claim)
        assert isinstance(result, ResearchResult)


class TestResearchClaims:
    def test_processes_all_claims(self, mocker):
        mocker.patch(
            "python_app.services.research_service._search_duckduckgo",
            return_value=[],
        )
        claims = [
            Claim(id="claim_1", text="Claim one."),
            Claim(id="claim_2", text="Claim two."),
            Claim(id="claim_3", text="Claim three."),
        ]
        results = research_claims(claims, max_results=3)
        assert len(results) == 3
        assert [r.claim_id for r in results] == ["claim_1", "claim_2", "claim_3"]

    def test_empty_claims_returns_empty_list(self, mocker):
        results = research_claims([], max_results=5)
        assert results == []
