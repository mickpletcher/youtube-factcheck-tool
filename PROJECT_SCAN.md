# Project Scan: youtube-factcheck-tool

**Scanned:** 2026-05-01  
**Branch:** main  
**Repo:** mickpletcher/youtube-factcheck-tool

---

## Overview

A FastAPI Python application that accepts a YouTube URL and produces a structured fact-check report. The pipeline fetches video metadata and a transcript, extracts factual claims via LLM, researches each claim via web search, scores each claim's validity, and returns a combined JSON + Markdown report.

---

## Repository Structure

```
youtube-factcheck-tool/
├── python_app/
│   ├── __init__.py
│   ├── config.py                  # Pydantic-settings config (env vars / .env file)
│   ├── main.py                    # FastAPI app factory + health endpoint
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # All Pydantic models
│   ├── routes/
│   │   ├── __init__.py
│   │   └── factcheck.py           # POST /factcheck route
│   └── services/
│       ├── __init__.py
│       ├── transcript_service.py  # Metadata + transcript extraction
│       ├── claim_extractor.py     # LLM / heuristic claim extraction
│       ├── research_service.py    # DuckDuckGo web search
│       ├── verdict_service.py     # LLM / heuristic verdict scoring
│       └── report_generator.py   # Credibility score + Markdown render
├── python_tests/
│   ├── __init__.py
│   ├── conftest.py                # Shared fixtures
│   ├── test_claim_extractor.py
│   ├── test_report_generator.py
│   ├── test_research_service.py
│   ├── test_routes.py
│   ├── test_transcript_service.py
│   └── test_verdict_service.py
├── requirements.txt
├── README.md
└── youtube-factcheck-tool.code-workspace
```

**Missing / expected but absent:**
- `.env.example` — referenced in README but not present in repo
- `Dockerfile` — no containerization provided
- `pytest.ini` / `pyproject.toml` — no pytest config file; relies on defaults
- `.gitignore` — not present (credentials in `.env` could accidentally be committed)

---

## Tech Stack

| Layer | Library | Version Constraint |
|---|---|---|
| Web framework | FastAPI | `>=0.111.0` |
| ASGI server | uvicorn[standard] | `>=0.29.0` |
| Data validation | pydantic | `>=2.7.0` |
| Settings | pydantic-settings | `>=2.2.0` |
| YouTube captions | youtube-transcript-api | `>=0.6.2` |
| Audio download | yt-dlp | `>=2024.4.9` |
| Audio transcription | openai-whisper | `>=20231117` |
| LLM | openai | `>=1.30.0` |
| Web search | duckduckgo-search | `>=6.1.0` |
| HTTP client | httpx | `>=0.27.0` |
| Form data | python-multipart | `>=0.0.9` |
| Env loading | python-dotenv | `>=1.0.1` |
| Test runner | pytest | `>=8.2.0` |
| Async tests | pytest-asyncio | `>=0.23.6` |
| Mocking | pytest-mock | `>=3.14.0` |

**External runtime dependency not in requirements.txt:** `ffmpeg` — required on the host for Whisper audio transcription (yt-dlp PostProcessor uses FFmpegExtractAudio).

---

## Configuration (`python_app/config.py`)

Loaded via `pydantic-settings`. Reads from `.env` file or environment.

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | `""` (empty) | OpenAI key for LLM claim extraction + verdict scoring |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model used for both LLM steps |
| `WHISPER_MODEL` | `base` | Whisper model size for audio fallback |
| `MAX_CLAIMS` | `10` | Cap on claims extracted per video |
| `RESEARCH_MAX_RESULTS` | `5` | DuckDuckGo results fetched per claim |

When `OPENAI_API_KEY` is empty, both the claim extractor and verdict scorer silently fall back to heuristic implementations — the app works without an API key, just less accurately.

---

## Data Models (`python_app/models/schemas.py`)

```
FactCheckRequest
  └── url: str (validated to require youtube.com or youtu.be)

VideoMetadata
  ├── video_id: str
  ├── title: str
  ├── channel: str
  ├── published_at: Optional[str]
  ├── duration_seconds: Optional[int]
  └── url: str

TranscriptSource (enum)
  ├── youtube_captions
  ├── audio_transcription
  └── unavailable

TranscriptResult
  ├── text: str
  ├── source: TranscriptSource
  └── language: Optional[str]

Claim
  ├── id: str        (e.g. "claim_1")
  └── text: str

SearchResult
  ├── title: str
  ├── url: str
  └── snippet: str

ResearchResult
  ├── claim_id: str
  ├── claim_text: str
  └── search_results: List[SearchResult]

VerdictLabel (enum)
  ├── Supported
  ├── Contradicted
  ├── Disputed
  └── Unverified

ScoredClaim
  ├── id: str
  ├── text: str
  ├── verdict: VerdictLabel
  ├── confidence: float (0.0–1.0)
  ├── explanation: str
  └── sources: List[str]

FactCheckReport  (final response shape)
  ├── video: VideoMetadata
  ├── transcript_source: TranscriptSource
  ├── claims: List[ScoredClaim]
  ├── summary: str
  ├── overall_credibility_score: float (0.0–1.0)
  └── report_markdown: str
```

---

## API Endpoints

### `GET /health`
Liveness probe. Returns `{"status": "ok"}`.

### `POST /factcheck`
**Request:**
```json
{ "url": "https://www.youtube.com/watch?v=VIDEO_ID" }
```
**Response:** `FactCheckReport` (JSON)

**Error codes:**
- `422` — URL fails Pydantic validation (not a YouTube link)
- `400` — `ValueError` raised during metadata extraction (e.g. unparseable URL)
- `502` — Any other exception during metadata fetch

Interactive docs available at `/docs` when server is running.

---

## Pipeline (Step-by-Step)

```
POST /factcheck
│
├─ 1. transcript_service.get_video_metadata(url)
│       └─ yt-dlp extract_info (skip_download=True)
│           └─ fallback: stub VideoMetadata from parsed URL
│
├─ 2. transcript_service.get_transcript(url)
│       ├─ _fetch_youtube_captions(video_id)
│       │     └─ youtube-transcript-api: manual EN → auto EN → None
│       └─ _transcribe_audio(url) if captions unavailable
│             └─ yt-dlp download bestaudio → FFmpegExtractAudio → mp3
│                   └─ whisper.load_model().transcribe(mp3)
│                         └─ fallback: TranscriptResult(source=unavailable)
│
├─ 3. claim_extractor.extract_claims(transcript_text)
│       ├─ LLM path (OpenAI chat completions, temp=0.2, max_tokens=1024)
│       │     └─ text truncated to 12,000 chars before sending
│       └─ heuristic fallback: sentence split + keyword regex filter
│
├─ 4. research_service.research_claims(claims)
│       └─ per claim: DDGS().text(f'fact check: "{claim.text}"', max_results=N*2)
│             └─ trusted-domain prioritisation, then trim to max_results
│
├─ 5. verdict_service.score_claims(research_results)
│       ├─ LLM path (OpenAI chat completions, temp=0.1, max_tokens=512)
│       └─ heuristic fallback: positive/negative keyword count in snippets
│
└─ 6. report_generator.generate_report(video, transcript_source, scored_claims)
        ├─ _compute_overall_score — confidence-weighted average of verdict scores
        │     Weights: Supported=1.0, Unverified=0.5, Disputed=0.25, Contradicted=0.0
        ├─ _build_summary — plain-English paragraph
        └─ _generate_markdown — full Markdown report string
```

---

## Service Details

### `transcript_service.py`

Supported URL formats for `_extract_video_id`:
- `youtube.com/watch?v=ID`
- `youtu.be/ID`
- `youtube.com/embed/ID`
- `youtube.com/shorts/ID`
- `m.youtube.com/watch?v=ID`

Caption preference order: manually-created EN/en-US/en-GB, then auto-generated. Concatenates all caption segment `text` fields with spaces.

Audio fallback uses `tempfile.TemporaryDirectory` — audio is cleaned up automatically. Looks for `audio.mp3`; falls back to any file in tmpdir if the exact name isn't found.

### `claim_extractor.py`

LLM system prompt instructs the model to return a raw JSON array of strings. Handles markdown code fence stripping and a regex fallback for embedded JSON arrays.

Heuristic fallback uses two regexes:
- Sentence boundary: `(?<=[.!?])\s+`
- Factual keywords: percent, million/billion/trillion, founded, born, died, invented, discovered, according, research, study, scientists, proved/proven, fact, evidence, data, statistics, report, published, recorded, measured, superlatives (largest, smallest, first, last, oldest, newest, highest, lowest)

Minimum sentence length for heuristic: 6 words.

### `research_service.py`

Trusted domains list (21 domains):
reuters.com, apnews.com, bbc.com, bbc.co.uk, nytimes.com, theguardian.com, washingtonpost.com, nature.com, science.org, scientificamerican.com, who.int, cdc.gov, nih.gov, nasa.gov, snopes.com, factcheck.org, politifact.com, fullfact.org, sciencedirect.com, pubmed.ncbi.nlm.nih.gov, britannica.com, history.com

Search query format: `fact check: "{claim.text}"` — fetches `max_results * 2` from DDGS then filters trusted to top, trims to `max_results`.

### `verdict_service.py`

LLM response schema enforced: `verdict`, `confidence`, `explanation`, `sources`. Confidence clamped to `[0.0, 1.0]`. Falls back gracefully on JSON parse failures.

Heuristic scoring thresholds:
- `pos > neg * 2` → Supported, confidence = `min(0.5 + pos/(total*2), 0.85)`
- `neg > pos * 2` → Contradicted, confidence = `min(0.5 + neg/(total*2), 0.85)`
- Else → Disputed, confidence = 0.4
- No signals → Unverified, confidence = 0.3

### `report_generator.py`

Overall credibility score: confidence-weighted mean of per-verdict weights. Verdict weight map: Supported=1.0, Unverified=0.5, Disputed=0.25, Contradicted=0.0. Returns 0.5 for empty claim lists.

Credibility assessment thresholds in summary text:
- `>= 0.75` → "largely credible"
- `>= 0.50` → "mixed credibility"
- `>= 0.25` → "significant inaccuracies or unverified claims"
- `< 0.25` → "largely inaccurate or contradicted by evidence"

---

## Test Coverage

All 7 service/route modules have corresponding test files.

| Test File | Classes/Functions Tested | Key Patterns |
|---|---|---|
| `test_transcript_service.py` | `_extract_video_id`, `get_video_metadata`, `get_transcript` | URL parsing edge cases, yt-dlp mock, caption/audio fallback mock |
| `test_claim_extractor.py` | `_extract_claims_heuristic`, `extract_claims` | Empty input, max_claims cap, LLM error fallback, API key branching |
| `test_research_service.py` | `_is_trusted`, `research_claim`, `research_claims` | Trusted domain check, DDGS mock, empty results, multi-claim ordering |
| `test_verdict_service.py` | `_score_claim_heuristic`, `score_claim` | Positive/negative/mixed/no signals, ScoredClaim return type |
| `test_report_generator.py` | `_compute_overall_score`, `_build_summary`, `_generate_markdown`, `generate_report` | Score edge cases, summary text content, Markdown structure |
| `test_routes.py` | `GET /health`, `POST /factcheck` | Full pipeline mock, 400/422/502 error codes, response shape |
| `conftest.py` | Shared fixtures | `client`, `sample_video_metadata`, `sample_transcript`, `sample_claims`, `sample_search_results`, `sample_research_results`, `sample_scored_claims` |

Tests use `pytest-mock` (`mocker.patch`) for all external dependencies (OpenAI, yt-dlp, youtube-transcript-api, DDGS). No integration tests or live API calls.

---

## Observed Issues and Gaps

### Security
- `OPENAI_API_KEY` stored in `.env` — no `.gitignore` present, risk of accidental commit
- No rate limiting on `POST /factcheck` — a single request triggers multiple external API calls and could be expensive or abused
- DuckDuckGo search results are trusted as-is; snippet content is passed to LLM without sanitization

### Functional
- `research_service` is synchronous — claims are researched sequentially, one DDGS call per claim. For `MAX_CLAIMS=10` this runs 10 serial web searches per request. No async or parallel execution.
- `verdict_service.score_claims` is also sequential — 10 serial OpenAI calls for 10 claims. No batching.
- Whisper model is loaded fresh every invocation (`whisper.load_model()` inside `_transcribe_audio`) — expensive if audio fallback is triggered repeatedly
- Transcript truncated to 12,000 chars for claim extraction; very long transcripts lose content
- No timeout handling on any external network calls (yt-dlp, DDGS, OpenAI)
- `report_markdown` field uses emoji (`✅`, `❌`, `⚠️`, `❓`) — may render inconsistently in some consumers

### Missing Infrastructure
- No `.env.example` file despite being referenced in README
- No `Dockerfile` or `docker-compose.yml`
- No `pyproject.toml` or `pytest.ini` — pytest settings (asyncio mode, markers) rely on defaults
- No `__version__` or version tracking beyond the hardcoded `"1.0.0"` in `main.py`
- No logging — all error paths are silently swallowed with bare `except Exception: pass` or `return None`

### Minor
- `httpx` is in requirements but not imported anywhere in the codebase — unused dependency
- `python-multipart` is in requirements but the API accepts only JSON bodies — unused dependency
- `TranscriptResult` has `language: Optional[str]` but `language` is never surfaced in the `FactCheckReport` response
- README says response status for non-YouTube URL is a "validation error" but the test asserts `422` (Pydantic validation), which is correct — README wording is slightly misleading

---

## How to Run

```bash
# Install deps
pip install -r requirements.txt

# Copy and fill in env
cp .env.example .env   # .env.example does not currently exist — create manually

# Start server
python -m uvicorn python_app.main:app --reload

# Run tests
python -m pytest python_tests -v
```

Server: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`
├── powershell_app/
│   └── .gitkeep
├── powershell_tests/
│   └── .gitkeep
