# Shared Contract

This document defines the shared request and response contract for the Python and PowerShell implementations in this repository.

## Scope

Both implementations should produce the same top level report shape for a single YouTube fact check request.

Current runtime surfaces:

1. Python API in `python_app`
2. Native PowerShell pipeline in `powershell_app`

## Request Contract

### Python API

Endpoint:

`POST /factcheck`

Body:

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

### PowerShell

Entry point:

`.\powershell_app\Invoke-YouTubeFactCheck.ps1 -Url "<youtube-url>"`

### Shared Request Rules

1. The input must be a YouTube URL from `youtube.com` or `youtu.be`
2. URL length must not exceed `2048` characters
3. The effective claim extraction count is capped at `25` even if configuration sets a larger value

## Response Contract

Top level shape:

```json
{
  "video": {
    "video_id": "dQw4w9WgXcQ",
    "title": "Example Title",
    "channel": "Example Channel",
    "published_at": "2024-01-01",
    "duration_seconds": 123,
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  },
  "transcript_source": "youtube_captions",
  "claims": [
    {
      "id": "claim_1",
      "text": "Example factual claim.",
      "verdict": "Supported",
      "confidence": 0.85,
      "explanation": "Why the claim was scored this way.",
      "sources": [
        "https://example.com/source"
      ]
    }
  ],
  "summary": "Overall summary text.",
  "overall_credibility_score": 0.72,
  "report_markdown": "# Fact Check Report\n..."
}
```

## Field Definitions

### `video`

Object with:

1. `video_id`
   YouTube video id
2. `title`
   Video title
3. `channel`
   Channel or uploader name
4. `published_at`
   Published date when available
5. `duration_seconds`
   Duration in seconds when available
6. `url`
   Original request URL

### `transcript_source`

Allowed values:

1. `youtube_captions`
2. `audio_transcription`
3. `unavailable`

### `claims`

Array of scored claim objects with:

1. `id`
   Claim id such as `claim_1`
2. `text`
   Claim text
3. `verdict`
   One of:
   `Supported`
   `Contradicted`
   `Disputed`
   `Unverified`
4. `confidence`
   Number from `0.0` to `1.0`
5. `explanation`
   Short explanation of the verdict
6. `sources`
   Array of source URLs used for the verdict

### `summary`

Plain language summary of the analyzed claims and overall assessment.

### `overall_credibility_score`

Number from `0.0` to `1.0`.

### `report_markdown`

Human readable Markdown version of the report.

## Shared Behavior Notes

1. If no factual claims are extracted, `claims` may be empty
2. If no claims are extracted, `overall_credibility_score` defaults to `0.5`
3. Both implementations may fall back from provider based logic to heuristic logic when providers fail or credentials are missing
4. Both implementations write the same top level contract even when internal provider paths differ

## Error Behavior

### Python

1. `422` for request validation failures such as non YouTube URLs or oversized URLs
2. `400` for invalid URL parsing failures during metadata handling
3. `502` for upstream metadata fetch failures

### PowerShell

1. Throws for invalid URLs
2. Throws for oversized URLs
3. Throws for missing required external tools
4. Clamps configured claim count to the contract limit before execution
