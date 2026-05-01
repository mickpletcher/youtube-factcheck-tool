"""Verdict service.

Determines whether each factual claim is Supported, Contradicted, Unverified,
or Disputed based on the research results.  Uses an LLM when an OpenAI API key
is available; otherwise falls back to a keyword-based heuristic.
"""

from __future__ import annotations

import json
import re
from typing import List

from python_app.models.schemas import ResearchResult, ScoredClaim, VerdictLabel

# ---------------------------------------------------------------------------
# LLM-based scoring
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a fact-checking expert. Given a factual claim and a list of web search
results, decide whether the claim is:
  - "Supported"     – the evidence clearly backs the claim
  - "Contradicted"  – the evidence clearly refutes the claim
  - "Disputed"      – evidence is mixed or conflicting
  - "Unverified"    – there is insufficient evidence to decide

Respond ONLY with a JSON object containing exactly these keys:
  "verdict":     one of the four labels above
  "confidence":  a float from 0.0 (very uncertain) to 1.0 (very certain)
  "explanation": a concise one-to-two sentence explanation
  "sources":     a JSON array of up to 3 URL strings that best support your verdict

Example:
{
  "verdict": "Supported",
  "confidence": 0.9,
  "explanation": "Multiple authoritative sources confirm this.",
  "sources": ["https://example.com/article"]
}
"""


def _score_claim_llm(
    research: ResearchResult,
    api_key: str,
    model: str,
) -> ScoredClaim:
    """Use the OpenAI chat completions API to score a claim."""
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=api_key)

    # Format search results as a readable block
    results_text = "\n".join(
        f"[{i + 1}] {r.title}\n    URL: {r.url}\n    Snippet: {r.snippet[:300]}"
        for i, r in enumerate(research.search_results)
    )

    user_content = (
        f"Claim: {research.claim_text}\n\n"
        f"Search Results:\n{results_text or 'No results found.'}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        max_tokens=512,
    )

    raw = response.choices[0].message.content or "{}"
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group()) if match else {}

    verdict_str = data.get("verdict", "Unverified")
    try:
        verdict = VerdictLabel(verdict_str)
    except ValueError:
        verdict = VerdictLabel.unverified

    confidence = float(data.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))

    explanation = data.get("explanation", "")
    sources: list = data.get("sources", [])
    if not isinstance(sources, list):
        sources = []

    return ScoredClaim(
        id=research.claim_id,
        text=research.claim_text,
        verdict=verdict,
        confidence=confidence,
        explanation=str(explanation),
        sources=[str(s) for s in sources],
    )


# ---------------------------------------------------------------------------
# Heuristic fallback
# ---------------------------------------------------------------------------

_POSITIVE_KEYWORDS = re.compile(
    r"\b(confirm|confirmed|true|accurate|correct|verified|fact|evidence|proven|"
    r"support|supported|valid|agree|agrees|agreed|yes|correct|right)\b",
    re.IGNORECASE,
)

_NEGATIVE_KEYWORDS = re.compile(
    r"\b(false|incorrect|wrong|debunked|myth|misleading|inaccurate|refuted|"
    r"disproven|contradict|contradicts|contradicted|no evidence|fake|hoax)\b",
    re.IGNORECASE,
)


def _score_claim_heuristic(research: ResearchResult) -> ScoredClaim:
    """Simple keyword-counting heuristic to assign a verdict."""
    all_text = " ".join(
        f"{r.title} {r.snippet}" for r in research.search_results
    )

    pos = len(_POSITIVE_KEYWORDS.findall(all_text))
    neg = len(_NEGATIVE_KEYWORDS.findall(all_text))
    total = pos + neg

    if total == 0:
        verdict = VerdictLabel.unverified
        confidence = 0.3
        explanation = "No relevant evidence was found in the search results."
    elif pos > neg * 2:
        verdict = VerdictLabel.supported
        confidence = min(0.5 + pos / (total * 2), 0.85)
        explanation = (
            f"Search results contain predominantly supportive language "
            f"({pos} positive vs {neg} negative signals)."
        )
    elif neg > pos * 2:
        verdict = VerdictLabel.contradicted
        confidence = min(0.5 + neg / (total * 2), 0.85)
        explanation = (
            f"Search results contain predominantly contradictory language "
            f"({neg} negative vs {pos} positive signals)."
        )
    else:
        verdict = VerdictLabel.disputed
        confidence = 0.4
        explanation = (
            f"Search results contain mixed signals "
            f"({pos} positive, {neg} negative)."
        )

    sources = [r.url for r in research.search_results[:3]]

    return ScoredClaim(
        id=research.claim_id,
        text=research.claim_text,
        verdict=verdict,
        confidence=round(confidence, 2),
        explanation=explanation,
        sources=sources,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_claim(
    research: ResearchResult,
    openai_api_key: str = "",
    openai_model: str = "gpt-4o-mini",
) -> ScoredClaim:
    """Return a :class:`~app.models.schemas.ScoredClaim` for *research*.

    Uses the OpenAI API when *openai_api_key* is provided; otherwise falls back
    to the heuristic scorer.
    """
    if openai_api_key:
        try:
            return _score_claim_llm(research, openai_api_key, openai_model)
        except Exception:
            pass  # fall through to heuristic

    return _score_claim_heuristic(research)


def score_claims(
    research_results: List[ResearchResult],
    openai_api_key: str = "",
    openai_model: str = "gpt-4o-mini",
) -> List[ScoredClaim]:
    """Score all claims in *research_results*.

    Args:
        research_results: List of research results to score.
        openai_api_key: OpenAI API key (empty → heuristic fallback).
        openai_model: OpenAI model name.

    Returns:
        List of :class:`~app.models.schemas.ScoredClaim` objects.
    """
    return [
        score_claim(r, openai_api_key=openai_api_key, openai_model=openai_model)
        for r in research_results
    ]
