"""Research service.

For each factual claim this service performs a web search and returns a list
of relevant snippets from trusted sources.  DuckDuckGo is used as the default
search back-end (no API key required).
"""

from __future__ import annotations

from typing import List

from app.models.schemas import Claim, ResearchResult, SearchResult

# Trusted source domains – results from these domains are prioritised
TRUSTED_DOMAINS = frozenset(
    {
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "bbc.co.uk",
        "nytimes.com",
        "theguardian.com",
        "washingtonpost.com",
        "nature.com",
        "science.org",
        "scientificamerican.com",
        "who.int",
        "cdc.gov",
        "nih.gov",
        "nasa.gov",
        "snopes.com",
        "factcheck.org",
        "politifact.com",
        "fullfact.org",
        "sciencedirect.com",
        "pubmed.ncbi.nlm.nih.gov",
        "britannica.com",
        "history.com",
    }
)


def _is_trusted(url: str) -> bool:
    """Return True if *url* belongs to a known trusted domain."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in TRUSTED_DOMAINS)


def _search_duckduckgo(query: str, max_results: int) -> List[SearchResult]:
    """Search DuckDuckGo and return up to *max_results* results."""
    try:
        from duckduckgo_search import DDGS  # type: ignore
    except ImportError:
        return []

    results: List[SearchResult] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results * 2):
                title = r.get("title", "")
                href = r.get("href", "")
                body = r.get("body", "")
                results.append(SearchResult(title=title, url=href, snippet=body))
    except Exception:
        return []

    # Put trusted sources first
    trusted = [r for r in results if _is_trusted(r.url)]
    others = [r for r in results if not _is_trusted(r.url)]
    return (trusted + others)[:max_results]


def research_claim(claim: Claim, max_results: int = 5) -> ResearchResult:
    """Search the web for evidence related to *claim*.

    Args:
        claim: The :class:`~app.models.schemas.Claim` to research.
        max_results: Maximum number of search results to return.

    Returns:
        A :class:`~app.models.schemas.ResearchResult` containing the search
        results for the claim.
    """
    query = f'fact check: "{claim.text}"'
    search_results = _search_duckduckgo(query, max_results)
    return ResearchResult(
        claim_id=claim.id,
        claim_text=claim.text,
        search_results=search_results,
    )


def research_claims(claims: List[Claim], max_results: int = 5) -> List[ResearchResult]:
    """Research each claim in *claims* and return results in the same order.

    Args:
        claims: List of claims to research.
        max_results: Maximum number of search results per claim.

    Returns:
        List of :class:`~app.models.schemas.ResearchResult` objects.
    """
    return [research_claim(claim, max_results=max_results) for claim in claims]
