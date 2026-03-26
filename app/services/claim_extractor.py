"""Claim extractor service.

Sends the transcript text to an LLM to identify distinct, verifiable factual
claims.  Falls back to a simple sentence-splitting heuristic when no OpenAI
API key is configured.
"""

from __future__ import annotations

import json
import re
from typing import List

from app.models.schemas import Claim


# ---------------------------------------------------------------------------
# LLM-based extraction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a fact-checking assistant. Your task is to identify distinct, verifiable
factual claims from the provided transcript text. A factual claim is a specific
statement that can be verified as true or false (e.g., statistics, historical
events, scientific statements, attributions). Exclude opinions, predictions, and
rhetorical questions.

Return ONLY a JSON array of claim strings. Example:
["The Earth is 4.5 billion years old.", "Water boils at 100°C at sea level."]
"""


def _extract_claims_llm(text: str, max_claims: int, api_key: str, model: str) -> List[Claim]:
    """Use the OpenAI chat completions API to extract claims from *text*."""
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=api_key)

    # Truncate to stay well within model context limits
    truncated = text[:12000]

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Extract up to {max_claims} key factual claims from this transcript:\n\n"
                    f"{truncated}"
                ),
            },
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content or "[]"

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip(), flags=re.MULTILINE)

    try:
        claim_texts: list = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract a JSON array embedded in the response
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            claim_texts = json.loads(match.group())
        else:
            claim_texts = []

    claims = []
    for idx, claim_text in enumerate(claim_texts[:max_claims], start=1):
        if isinstance(claim_text, str) and claim_text.strip():
            claims.append(Claim(id=f"claim_{idx}", text=claim_text.strip()))

    return claims


# ---------------------------------------------------------------------------
# Heuristic fallback
# ---------------------------------------------------------------------------

# Sentence boundary pattern
_SENT_RE = re.compile(r"(?<=[.!?])\s+")

# Keywords that suggest a factual statement
_FACTUAL_KEYWORDS = re.compile(
    r"\b(percent|%|million|billion|trillion|founded|born|died|invented|discovered|"
    r"according|research|study|studies|scientists|proved|proven|fact|evidence|"
    r"data|statistics|statistic|report|reported|published|recorded|measured|"
    r"largest|smallest|first|last|oldest|newest|highest|lowest)\b",
    re.IGNORECASE,
)


def _extract_claims_heuristic(text: str, max_claims: int) -> List[Claim]:
    """Simple fallback: return sentences that look like factual statements."""
    sentences = _SENT_RE.split(text)
    factual = [s.strip() for s in sentences if _FACTUAL_KEYWORDS.search(s) and len(s.split()) >= 6]
    claims = []
    for idx, sentence in enumerate(factual[:max_claims], start=1):
        claims.append(Claim(id=f"claim_{idx}", text=sentence))
    return claims


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_claims(
    transcript_text: str,
    max_claims: int = 10,
    openai_api_key: str = "",
    openai_model: str = "gpt-4o-mini",
) -> List[Claim]:
    """Extract factual claims from *transcript_text*.

    Uses the OpenAI API when *openai_api_key* is provided; otherwise falls back
    to a heuristic sentence-level filter.

    Args:
        transcript_text: Raw transcript string.
        max_claims: Maximum number of claims to return.
        openai_api_key: OpenAI API key (empty string → use heuristic fallback).
        openai_model: OpenAI model name.

    Returns:
        A list of :class:`~app.models.schemas.Claim` objects.
    """
    if not transcript_text.strip():
        return []

    if openai_api_key:
        try:
            return _extract_claims_llm(
                transcript_text, max_claims, openai_api_key, openai_model
            )
        except Exception:
            pass  # fall through to heuristic

    return _extract_claims_heuristic(transcript_text, max_claims)
