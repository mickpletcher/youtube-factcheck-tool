"""Tests for the claim extractor service."""

import pytest

from app.services.claim_extractor import _extract_claims_heuristic, extract_claims
from app.models.schemas import Claim


class TestExtractClaimsHeuristic:
    def test_returns_claims_for_factual_sentences(self):
        text = (
            "Scientists have discovered that the Earth is 4.5 billion years old. "
            "According to research, 80 percent of the ocean is unexplored. "
            "I love pizza."
        )
        claims = _extract_claims_heuristic(text, max_claims=10)
        assert len(claims) >= 1
        assert all(isinstance(c, Claim) for c in claims)

    def test_respects_max_claims(self):
        # Build a long text with many factual sentences
        sentences = [
            f"According to research, {i} percent of something is true."
            for i in range(20)
        ]
        text = " ".join(sentences)
        claims = _extract_claims_heuristic(text, max_claims=5)
        assert len(claims) <= 5

    def test_assigns_sequential_ids(self):
        text = (
            "According to a study, 50 percent of adults sleep less than 7 hours. "
            "Scientists recorded evidence that humans have 206 bones."
        )
        claims = _extract_claims_heuristic(text, max_claims=10)
        for idx, claim in enumerate(claims, start=1):
            assert claim.id == f"claim_{idx}"

    def test_empty_text_returns_empty_list(self):
        assert _extract_claims_heuristic("", max_claims=10) == []

    def test_no_factual_sentences_returns_empty_list(self):
        text = "I think this is great. You should try it. Let me know what you think."
        claims = _extract_claims_heuristic(text, max_claims=10)
        assert claims == []


class TestExtractClaims:
    def test_empty_transcript_returns_empty(self):
        result = extract_claims("", openai_api_key="")
        assert result == []

    def test_whitespace_only_returns_empty(self):
        result = extract_claims("   \n\t  ", openai_api_key="")
        assert result == []

    def test_heuristic_used_when_no_api_key(self):
        text = (
            "According to scientists, the Moon is 384,400 km from Earth. "
            "Research shows that 70 percent of the planet is covered by water."
        )
        claims = extract_claims(text, max_claims=10, openai_api_key="")
        assert isinstance(claims, list)
        assert all(isinstance(c, Claim) for c in claims)

    def test_falls_back_to_heuristic_on_llm_error(self, mocker):
        mocker.patch(
            "app.services.claim_extractor._extract_claims_llm",
            side_effect=Exception("API error"),
        )
        text = (
            "According to scientists, the Moon is 384,400 km from Earth. "
            "Studies show that 70 percent of the planet is covered by water."
        )
        claims = extract_claims(text, openai_api_key="sk-fake-key")
        assert isinstance(claims, list)

    def test_llm_path_used_when_api_key_present(self, mocker):
        expected = [Claim(id="claim_1", text="Earth is round.")]
        mock_llm = mocker.patch(
            "app.services.claim_extractor._extract_claims_llm",
            return_value=expected,
        )
        result = extract_claims("Some text.", openai_api_key="sk-fake-key")
        mock_llm.assert_called_once()
        assert result == expected
