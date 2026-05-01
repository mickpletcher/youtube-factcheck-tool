"""Report generator service.

Converts the pipeline results into a structured :class:`FactCheckReport` that
includes both machine-readable JSON (the model itself) and a human-readable
Markdown string.
"""

from __future__ import annotations

from typing import List

from python_app.models.schemas import (
    FactCheckReport,
    ScoredClaim,
    TranscriptSource,
    VideoMetadata,
    VerdictLabel,
)

# ---------------------------------------------------------------------------
# Credibility score
# ---------------------------------------------------------------------------

_VERDICT_WEIGHT: dict[VerdictLabel, float] = {
    VerdictLabel.supported: 1.0,
    VerdictLabel.unverified: 0.5,
    VerdictLabel.disputed: 0.25,
    VerdictLabel.contradicted: 0.0,
}


def _compute_overall_score(claims: List[ScoredClaim]) -> float:
    """Return a 0–1 credibility score weighted by claim confidence."""
    if not claims:
        return 0.5  # neutral when no claims were extracted

    total_weight = 0.0
    weighted_score = 0.0
    for claim in claims:
        weight = claim.confidence
        total_weight += weight
        weighted_score += _VERDICT_WEIGHT[claim.verdict] * weight

    if total_weight == 0:
        return 0.5

    return round(weighted_score / total_weight, 2)


def _build_summary(claims: List[ScoredClaim], overall_score: float) -> str:
    """Generate a plain-English summary paragraph."""
    if not claims:
        return "No factual claims could be extracted from this video."

    counts: dict[str, int] = {}
    for claim in claims:
        label = claim.verdict.value
        counts[label] = counts.get(label, 0) + 1

    breakdown = ", ".join(f"{v}: {n}" for v, n in sorted(counts.items()))
    pct = int(overall_score * 100)

    if overall_score >= 0.75:
        assessment = "The content appears to be largely credible."
    elif overall_score >= 0.5:
        assessment = "The content has mixed credibility."
    elif overall_score >= 0.25:
        assessment = "The content contains significant inaccuracies or unverified claims."
    else:
        assessment = "The content is largely inaccurate or contradicted by evidence."

    return (
        f"Analysed {len(claims)} claim(s) from this video "
        f"({breakdown}). "
        f"Overall credibility score: {pct}%. "
        f"{assessment}"
    )


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

_VERDICT_EMOJI: dict[VerdictLabel, str] = {
    VerdictLabel.supported: "✅",
    VerdictLabel.contradicted: "❌",
    VerdictLabel.disputed: "⚠️",
    VerdictLabel.unverified: "❓",
}


def _generate_markdown(
    video: VideoMetadata,
    transcript_source: TranscriptSource,
    claims: List[ScoredClaim],
    summary: str,
    overall_score: float,
) -> str:
    """Render the fact-check report as a Markdown string."""
    lines: list[str] = []

    lines.append("# Fact-Check Report")
    lines.append("")

    # Video metadata
    lines.append("## Video Information")
    lines.append("")
    lines.append(f"- **Title:** {video.title}")
    lines.append(f"- **Channel:** {video.channel}")
    if video.published_at:
        lines.append(f"- **Published:** {video.published_at}")
    if video.duration_seconds is not None:
        minutes, seconds = divmod(video.duration_seconds, 60)
        lines.append(f"- **Duration:** {minutes}m {seconds:02d}s")
    lines.append(f"- **URL:** {video.url}")
    lines.append(f"- **Transcript source:** {transcript_source.value.replace('_', ' ').title()}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")
    lines.append(f"**Overall Credibility Score: {int(overall_score * 100)}%**")
    lines.append("")

    # Claims
    if claims:
        lines.append("## Claim-by-Claim Analysis")
        lines.append("")
        for claim in claims:
            emoji = _VERDICT_EMOJI[claim.verdict]
            lines.append(
                f"### {emoji} {claim.id.replace('_', ' ').title()}: "
                f"{claim.verdict.value} ({int(claim.confidence * 100)}% confidence)"
            )
            lines.append("")
            lines.append(f"> {claim.text}")
            lines.append("")
            lines.append(f"**Explanation:** {claim.explanation}")
            if claim.sources:
                lines.append("")
                lines.append("**Sources:**")
                for src in claim.sources:
                    lines.append(f"- {src}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_report(
    video: VideoMetadata,
    transcript_source: TranscriptSource,
    scored_claims: List[ScoredClaim],
) -> FactCheckReport:
    """Build and return a complete :class:`FactCheckReport`.

    Args:
        video: Video metadata.
        transcript_source: How the transcript was obtained.
        scored_claims: List of scored claims from the verdict service.

    Returns:
        A :class:`~app.models.schemas.FactCheckReport` with all fields
        populated, including the rendered Markdown report.
    """
    overall_score = _compute_overall_score(scored_claims)
    summary = _build_summary(scored_claims, overall_score)
    markdown = _generate_markdown(
        video=video,
        transcript_source=transcript_source,
        claims=scored_claims,
        summary=summary,
        overall_score=overall_score,
    )

    return FactCheckReport(
        video=video,
        transcript_source=transcript_source,
        claims=scored_claims,
        summary=summary,
        overall_credibility_score=overall_score,
        report_markdown=markdown,
    )
