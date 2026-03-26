# YouTube Fact-Check Tool

A Python FastAPI application that accepts a YouTube URL, extracts video metadata, pulls the transcript (or falls back to audio transcription), extracts factual claims, researches those claims against trusted sources, scores their validity, and generates a final report in JSON and Markdown.

## Features

- **Transcript extraction**: Uses `youtube-transcript-api` to fetch available captions; falls back to audio download (via `yt-dlp`) + speech-to-text (via `openai-whisper`) when no transcript is available.
- **Claim extraction**: Sends the transcript to an LLM (OpenAI GPT) to identify distinct factual claims.
- **Research**: Searches the web (DuckDuckGo by default; configurable) for evidence supporting or contradicting each claim.
- **Verdict scoring**: Rates each claim as *Supported*, *Contradicted*, *Unverified*, or *Disputed* with a 0–1 confidence score.
- **Report generation**: Returns a structured `FactCheckReport` as both JSON and Markdown.

## Project Structure

```
app/
├── main.py                  # FastAPI application entry point
├── config.py                # Environment-based settings
├── models/
│   └── schemas.py           # Pydantic data models
├── routes/
│   └── factcheck.py         # /factcheck endpoint
└── services/
    ├── transcript_service.py  # Transcript extraction & metadata
    ├── claim_extractor.py     # Factual claim identification
    ├── research_service.py    # Web research per claim
    ├── verdict_service.py     # Validity scoring
    └── report_generator.py    # JSON & Markdown report generation
tests/
├── conftest.py
├── test_transcript_service.py
├── test_claim_extractor.py
├── test_research_service.py
├── test_verdict_service.py
├── test_report_generator.py
└── test_routes.py
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes (for LLM features) | OpenAI API key used for claim extraction and verdict scoring |
| `OPENAI_MODEL` | No (default: `gpt-4o-mini`) | OpenAI model name |
| `MAX_CLAIMS` | No (default: `10`) | Maximum number of claims to extract per video |
| `RESEARCH_MAX_RESULTS` | No (default: `5`) | Number of search results to fetch per claim |
| `WHISPER_MODEL` | No (default: `base`) | Whisper model size for audio transcription fallback |

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

## API Usage

### `POST /factcheck`

**Request body:**

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

**Response:**

```json
{
  "video": {
    "video_id": "dQw4w9WgXcQ",
    "title": "...",
    "channel": "...",
    "published_at": "...",
    "duration_seconds": 212,
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  },
  "transcript_source": "youtube_captions",
  "claims": [
    {
      "id": "claim_1",
      "text": "...",
      "verdict": "Supported",
      "confidence": 0.85,
      "explanation": "...",
      "sources": ["https://..."]
    }
  ],
  "summary": "...",
  "overall_credibility_score": 0.72,
  "report_markdown": "# Fact-Check Report\n..."
}
```

### `GET /health`

Returns `{"status": "ok"}` – useful for container health checks.

## Running Tests

```bash
pytest tests/ -v
```

## Architecture Notes

- Each service is stateless and receives its dependencies via constructor injection, making unit testing straightforward.
- When `OPENAI_API_KEY` is not set, the claim extractor and verdict service fall back to simple heuristic/rule-based logic so the application still starts and returns results.
- Audio transcription is only triggered when the YouTube video has no available captions; it requires `ffmpeg` to be installed on the system.
